import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

import numpy as np

DEFAULT_MODEL_PATH = str(
    Path(__file__).resolve().parent.parent / "models" / "finbert-finetuned"
)
FALLBACK_MODEL_NAME = "ProsusAI/finbert"
MODEL_NAME = os.environ.get("FINBERT_MODEL_NAME", DEFAULT_MODEL_PATH)
MAX_LEN = int(os.environ.get("FINBERT_MAX_LEN", "512"))

LABEL_MAP = {
    0: "positive",
    1: "negative",
    2: "neutral",
}

SENTIMENT_TTL_SECONDS = 5 * 60


@dataclass
class FinBERTSentimentPipeline:
    tokenizer: object
    model: object
    device: object

    @classmethod
    def load(cls) -> "FinBERTSentimentPipeline":
        model_name = resolve_model_name()
        try:
            import torch
            from transformers import AutoModelForSequenceClassification, AutoTokenizer
        except Exception:
            raise RuntimeError("transformers runtime is unavailable")

        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForSequenceClassification.from_pretrained(model_name)
        model.to(device)
        model.eval()
        return cls(tokenizer=tokenizer, model=model, device=device)

    def score(self, texts: List[str]) -> List[Dict]:
        cleaned = [text if isinstance(text, str) else "" for text in texts]
        if not cleaned:
            return []

        encoded = self.tokenizer(
            cleaned,
            padding=True,
            truncation=True,
            max_length=MAX_LEN,
            return_tensors="pt",
        )
        encoded = {key: value.to(self.device) for key, value in encoded.items()}

        import torch

        with torch.no_grad():
            logits = self.model(**encoded).logits.detach().cpu().numpy()

        probabilities = _softmax(logits)
        results = []
        for text, probs in zip(cleaned, probabilities):
            positive = float(probs[0])
            negative = float(probs[1])
            neutral = float(probs[2])
            sentiment_score = positive - negative
            sentiment_label = LABEL_MAP[int(probs.argmax())]
            results.append(
                {
                    "text": text,
                    "sentiment_label": sentiment_label,
                    "sentiment_score": round(sentiment_score, 4),
                }
            )
        return results


class HeuristicSentimentPipeline:
    POSITIVE_TERMS = {
        "beat", "gain", "growth", "bullish", "rally", "surge", "strong", "upgrade",
        "buy", "outperform", "profit", "profits", "record", "expansion", "optimistic"
    }
    NEGATIVE_TERMS = {
        "miss", "loss", "drop", "fall", "bearish", "slump", "weak", "downgrade",
        "sell", "underperform", "risk", "fraud", "decline", "cut", "cuts", "warning"
    }

    def score(self, texts: List[str]) -> List[Dict]:
        results = []
        for raw_text in texts:
            text = raw_text if isinstance(raw_text, str) else ""
            lower = text.lower()
            positive_hits = sum(term in lower for term in self.POSITIVE_TERMS)
            negative_hits = sum(term in lower for term in self.NEGATIVE_TERMS)
            raw_score = positive_hits - negative_hits
            sentiment_score = max(-1.0, min(1.0, raw_score / 4.0))
            if sentiment_score > 0.1:
                label = "positive"
            elif sentiment_score < -0.1:
                label = "negative"
            else:
                label = "neutral"
            results.append(
                {
                    "text": text,
                    "sentiment_label": label,
                    "sentiment_score": round(float(sentiment_score), 4),
                }
            )
        return results


_PIPELINE = None


def resolve_model_name() -> str:
    configured = MODEL_NAME.strip()
    if not configured:
        return FALLBACK_MODEL_NAME

    candidate = Path(configured)
    if candidate.is_absolute() or configured.startswith(".") or "/" in configured:
        if candidate.exists():
            return str(candidate)
        return FALLBACK_MODEL_NAME

    return configured


def get_pipeline() -> FinBERTSentimentPipeline:
    global _PIPELINE
    if _PIPELINE is None:
        try:
            _PIPELINE = FinBERTSentimentPipeline.load()
        except Exception:
            _PIPELINE = HeuristicSentimentPipeline()
    return _PIPELINE


def _softmax(logits):
    shifted = logits - np.max(logits, axis=1, keepdims=True)
    exp_values = np.exp(shifted)
    return exp_values / np.sum(exp_values, axis=1, keepdims=True)


def score_texts(texts: List[str]) -> List[Dict]:
    return get_pipeline().score(texts)


def sentiment_score(text: str) -> Dict:
    if not text:
        return {"label": "neutral", "score": 0.0}

    result = score_texts([text])[0]
    return {
        "label": result["sentiment_label"],
        "score": result["sentiment_score"],
    }


def _to_datetime(value):
    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, str):
        normalized = value.replace("Z", "+00:00")
        dt = datetime.fromisoformat(normalized)
    else:
        raise TypeError("timestamps must be datetime objects or ISO-8601 strings")

    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def compute_ewma_score(ticker, scores, timestamps) -> float:
    if len(scores) != len(timestamps):
        raise ValueError("scores and timestamps must have the same length")
    if not scores:
        return 0.0

    paired = sorted(
        zip((_to_datetime(ts) for ts in timestamps), scores),
        key=lambda item: item[0],
    )
    halflife_seconds = 30 * 60
    alpha = 1.0
    ewma = float(paired[0][1])
    previous_ts = paired[0][0]

    for current_ts, score in paired[1:]:
        elapsed = max((current_ts - previous_ts).total_seconds(), 0.0)
        decay = 0.5 ** (elapsed / halflife_seconds)
        alpha = 1.0 - decay
        ewma = alpha * float(score) + (1.0 - alpha) * ewma
        previous_ts = current_ts

    return round(float(ewma), 4)


def cache_sentiment_score(ticker, source, score, redis_client):
    key = f"sentiment:{source}:{ticker}"
    redis_client.setex(key, SENTIMENT_TTL_SECONDS, str(float(score)))
