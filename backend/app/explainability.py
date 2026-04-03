import asyncio
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import joblib
import numpy as np
import pandas as pd
import xgboost as xgb
from redis import Redis

try:
    import shap  # type: ignore
except ImportError:  # pragma: no cover - exercised through fallback path
    shap = None

DEFAULT_MODEL_PATH = Path(__file__).resolve().parent.parent / "models" / "xgboost_signal_model.joblib"
TRAINING_DATA_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "training_features.csv"
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
EXPLANATION_TTL_SECONDS = int(os.environ.get("EXPLANATION_TTL_SECONDS", "900"))

redis = Redis.from_url(REDIS_URL)

FEATURE_LABELS = {
    "price_delta_1d": "1 day price move",
    "price_delta_5d": "5 day price trend",
    "rsi_14": "RSI momentum",
    "ma_cross": "moving average crossover",
    "price_vs_ma20": "price vs 20 day average",
    "volume_spike_zscore": "volume spike",
    "sentiment_news": "news sentiment",
    "sentiment_social": "social sentiment",
    "sentiment_divergence": "sentiment-price divergence",
}


@dataclass
class SignalModelBundle:
    model: object
    feature_columns: List[str]
    int_to_label: Dict[int, str]
    metrics: Dict[str, float]
    _explainer: Optional[object] = field(default=None, init=False, repr=False)

    def get_tree_explainer(self):
        if shap is None:
            return None
        if self._explainer is None:
            self._explainer = shap.TreeExplainer(self.model)
        return self._explainer


_MODEL_BUNDLE: Optional[SignalModelBundle] = None


def load_model_bundle() -> SignalModelBundle:
    global _MODEL_BUNDLE
    if _MODEL_BUNDLE is None:
        payload = joblib.load(DEFAULT_MODEL_PATH)
        _MODEL_BUNDLE = SignalModelBundle(
            model=payload["model"],
            feature_columns=list(payload["feature_columns"]),
            int_to_label={int(key): value for key, value in payload["int_to_label"].items()},
            metrics=dict(payload.get("metrics", {})),
        )
    return _MODEL_BUNDLE


def load_latest_training_row(ticker: str, data_path: Path = TRAINING_DATA_PATH) -> Dict:
    df = pd.read_csv(data_path, parse_dates=["date"])
    rows = df.loc[df["ticker"].str.upper() == ticker.upper()].sort_values("date")
    if rows.empty:
        raise KeyError(f"Ticker {ticker} not found in training data")
    row = rows.iloc[-1].to_dict()
    row["date"] = rows.iloc[-1]["date"].strftime("%Y-%m-%d")
    row["ticker"] = ticker.upper()
    return row


def _coerce_feature_frame(feature_payload: Dict, feature_columns: List[str]) -> pd.DataFrame:
    row = {}
    for feature_name in feature_columns:
        row[feature_name] = float(feature_payload.get(feature_name, 0.0) or 0.0)
    return pd.DataFrame([row], columns=feature_columns)


def _format_feature_value(feature_name: str, value: float) -> str:
    if feature_name in {"price_delta_1d", "price_delta_5d", "price_vs_ma20"}:
        return f"{value * 100:.2f}%"
    if feature_name == "rsi_14":
        return f"{value:.1f}"
    if feature_name == "ma_cross":
        return "bullish" if value >= 1 else "bearish"
    if feature_name == "volume_spike_zscore":
        return f"z-score {value:+.2f}"
    if feature_name in {"sentiment_news", "sentiment_social", "sentiment_divergence"}:
        return f"{value:+.3f}"
    return f"{value:.4f}"


def _coerce_shap_array(values, row_count: int, feature_count: int) -> np.ndarray:
    if isinstance(values, list):
        return np.stack([np.asarray(item) for item in values], axis=1)

    array = np.asarray(values)
    if array.ndim == 2:
        return array[:, np.newaxis, :]
    if array.ndim != 3:
        raise ValueError(f"Unexpected SHAP output shape: {array.shape}")

    if array.shape == (row_count, feature_count, array.shape[2]):
        return np.swapaxes(array, 1, 2)
    if array.shape[0] == row_count and array.shape[2] == feature_count:
        return array
    if array.shape[1] == row_count and array.shape[2] == feature_count:
        return np.swapaxes(array, 0, 1)
    raise ValueError(f"Unable to normalize SHAP output shape: {array.shape}")


def _compute_tree_shap_values(bundle: SignalModelBundle, feature_frame: pd.DataFrame) -> Optional[np.ndarray]:
    explainer = bundle.get_tree_explainer()
    if explainer is None:
        return None

    try:
        explanation = explainer(feature_frame[bundle.feature_columns])
        values = getattr(explanation, "values", explanation)
    except Exception:
        values = explainer.shap_values(feature_frame[bundle.feature_columns])
    return _coerce_shap_array(values, len(feature_frame), len(bundle.feature_columns))


def _compute_native_contrib_values(bundle: SignalModelBundle, feature_frame: pd.DataFrame) -> np.ndarray:
    matrix = xgb.DMatrix(feature_frame[bundle.feature_columns], feature_names=bundle.feature_columns)
    contributions = bundle.model.get_booster().predict(
        matrix,
        pred_contribs=True,
        strict_shape=True,
    )
    if contributions.ndim != 3:
        raise ValueError(f"Unexpected XGBoost contribution shape: {contributions.shape}")
    return contributions[:, :, :-1]


def _predict_signal(bundle: SignalModelBundle, feature_frame: pd.DataFrame) -> Dict:
    probabilities = bundle.model.predict_proba(feature_frame[bundle.feature_columns])[0]
    predicted_index = int(np.argmax(probabilities))
    return {
        "predicted_index": predicted_index,
        "label": bundle.int_to_label[predicted_index],
        "confidence": round(float(probabilities[predicted_index]), 4),
        "probabilities": {
            bundle.int_to_label[index]: round(float(score), 4)
            for index, score in enumerate(probabilities)
        },
    }


def _rank_feature_impacts(
    feature_frame: pd.DataFrame,
    shap_values: np.ndarray,
    bundle: SignalModelBundle,
    predicted_index: int,
) -> List[Dict]:
    row = feature_frame.iloc[0]
    class_values = shap_values[0][predicted_index]
    ranked = []
    for feature_name, shap_value in zip(bundle.feature_columns, class_values):
        ranked.append(
            {
                "feature": feature_name,
                "label": FEATURE_LABELS.get(feature_name, feature_name.replace("_", " ")),
                "value": round(float(row[feature_name]), 6),
                "display_value": _format_feature_value(feature_name, float(row[feature_name])),
                "shap_value": round(float(shap_value), 6),
                "effect": "supports" if float(shap_value) >= 0 else "tempers",
            }
        )
    ranked.sort(key=lambda item: abs(item["shap_value"]), reverse=True)
    return ranked


def render_explanation_text(signal_label: str, confidence: float, top_factors: List[Dict]) -> Dict:
    supporting = [item for item in top_factors if item["effect"] == "supports"]
    tempering = [item for item in top_factors if item["effect"] == "tempers"]

    summary_parts = []
    if supporting:
        leaders = ", ".join(item["label"] for item in supporting[:2])
        summary_parts.append(f"Strongest support comes from {leaders}.")
    if tempering:
        summary_parts.append(f"Main drag comes from {tempering[0]['label']}.")
    if not summary_parts:
        summary_parts.append("Feature impacts are balanced around the decision boundary.")

    details = []
    for factor in top_factors:
        details.append(
            f"{factor['label']} {factor['effect']} the {signal_label} call "
            f"(value {factor['display_value']}, SHAP {factor['shap_value']:+.3f})."
        )

    return {
        "headline": f"{signal_label} with {confidence * 100:.1f}% confidence.",
        "summary": " ".join(summary_parts),
        "details": details,
    }


def build_signal_explanation(ticker: str, feature_payload: Dict) -> Dict:
    bundle = load_model_bundle()
    feature_frame = _coerce_feature_frame(feature_payload, bundle.feature_columns)
    prediction = _predict_signal(bundle, feature_frame)

    shap_values = _compute_tree_shap_values(bundle, feature_frame)
    explainer_name = "shap_tree"
    if shap_values is None:
        shap_values = _compute_native_contrib_values(bundle, feature_frame)
        explainer_name = "xgboost_pred_contribs_fallback"

    ranked_factors = _rank_feature_impacts(
        feature_frame=feature_frame,
        shap_values=shap_values,
        bundle=bundle,
        predicted_index=prediction["predicted_index"],
    )
    top_factors = ranked_factors[:3]

    explanation = {
        "ticker": ticker.upper(),
        "as_of": str(feature_payload.get("date", "unknown")),
        "signal": {
            "label": prediction["label"],
            "confidence": prediction["confidence"],
            "probabilities": prediction["probabilities"],
        },
        "model": {
            "explainer": explainer_name,
            "feature_count": len(bundle.feature_columns),
            "training_metrics": bundle.metrics,
        },
        "narrative": render_explanation_text(
            signal_label=prediction["label"],
            confidence=prediction["confidence"],
            top_factors=top_factors,
        ),
        "top_factors": top_factors,
    }
    return explanation


def explanation_cache_key(ticker: str) -> str:
    return f"explanation:signal:{ticker.upper()}"


def cache_signal_explanation(ticker: str, payload: Dict, redis_client=None) -> bool:
    client = redis_client or redis
    try:
        client.setex(
            explanation_cache_key(ticker),
            EXPLANATION_TTL_SECONDS,
            json.dumps(payload),
        )
        return True
    except Exception:
        return False


def get_cached_signal_explanation(ticker: str, redis_client=None) -> Optional[Dict]:
    client = redis_client or redis
    try:
        payload = client.get(explanation_cache_key(ticker))
    except Exception:
        return None
    if not payload:
        return None
    if isinstance(payload, bytes):
        payload = payload.decode("utf-8")
    return json.loads(payload)


async def precompute_signal_explanation(ticker: str, feature_payload: Dict, redis_client=None) -> Dict:
    explanation = await asyncio.to_thread(build_signal_explanation, ticker, feature_payload)
    cache_signal_explanation(ticker, explanation, redis_client=redis_client)
    return explanation
