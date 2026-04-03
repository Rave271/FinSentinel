import os
from typing import Dict, List, Optional

from redis import Redis

from . import explainability, sentiment, storage


REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
PRICE_DELTA_CLIP = 0.05

redis = Redis.from_url(REDIS_URL)


def _safe_float(value, default=0.0) -> float:
    try:
        if value in ("", None):
            return float(default)
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def normalize_price_delta(price_delta_1d: float) -> float:
    clipped = max(-PRICE_DELTA_CLIP, min(PRICE_DELTA_CLIP, _safe_float(price_delta_1d)))
    return round(clipped / PRICE_DELTA_CLIP, 4)


def _load_cached_sentiment(ticker: str, source: str, redis_client=None) -> Optional[float]:
    client = redis_client or redis
    key = f"sentiment:{source}:{ticker.upper()}"
    try:
        payload = client.get(key)
    except Exception:
        return None
    if payload is None:
        return None
    if isinstance(payload, bytes):
        payload = payload.decode("utf-8")
    return _safe_float(payload)


def _merge_live_sentiment(base_row: Dict, redis_client=None) -> Dict:
    merged = dict(base_row)
    ticker = str(merged["ticker"]).upper()
    news_score = _load_cached_sentiment(ticker, "news", redis_client=redis_client)
    social_score = _load_cached_sentiment(ticker, "social", redis_client=redis_client)
    if news_score is not None:
        merged["sentiment_news"] = round(news_score, 4)
    if social_score is not None:
        merged["sentiment_social"] = round(social_score, 4)

    price_delta_normalized = normalize_price_delta(merged.get("price_delta_1d", 0.0))
    composite_sentiment = round(
        (
            _safe_float(merged.get("sentiment_news", 0.0))
            + _safe_float(merged.get("sentiment_social", 0.0))
        )
        / 2.0,
        4,
    )
    merged["sentiment_divergence"] = round(abs(composite_sentiment - price_delta_normalized), 4)
    merged["price_delta_normalized"] = price_delta_normalized
    merged["composite_sentiment"] = composite_sentiment
    return merged


def build_divergence_snapshot(ticker: str, redis_client=None) -> Dict:
    feature_row = explainability.load_latest_training_row(ticker)
    merged = _merge_live_sentiment(feature_row, redis_client=redis_client)
    mismatch = merged["price_delta_normalized"] * merged["composite_sentiment"] < 0
    score = merged["sentiment_divergence"]
    if score >= 1.0:
        severity = "high"
    elif score >= 0.5:
        severity = "medium"
    else:
        severity = "low"

    return {
        "ticker": ticker.upper(),
        "as_of": merged.get("date"),
        "price_delta_1d": round(_safe_float(merged.get("price_delta_1d")), 6),
        "price_delta_normalized": merged["price_delta_normalized"],
        "news_sentiment": round(_safe_float(merged.get("sentiment_news")), 4),
        "social_sentiment": round(_safe_float(merged.get("sentiment_social")), 4),
        "composite_sentiment": merged["composite_sentiment"],
        "divergence_score": score,
        "severity": severity,
        "signal_mismatch": mismatch,
    }


def build_signal_snapshot(ticker: str, redis_client=None) -> Dict:
    feature_row = explainability.load_latest_training_row(ticker)
    merged = _merge_live_sentiment(feature_row, redis_client=redis_client)
    explanation = explainability.build_signal_explanation(ticker, merged)
    divergence = build_divergence_snapshot(ticker, redis_client=redis_client)

    return {
        "ticker": ticker.upper(),
        "as_of": merged.get("date"),
        "market": {
            "close": round(_safe_float(merged.get("close")), 4),
            "open": round(_safe_float(merged.get("open")), 4),
            "high": round(_safe_float(merged.get("high")), 4),
            "low": round(_safe_float(merged.get("low")), 4),
            "volume": int(_safe_float(merged.get("volume"))),
            "price_delta_1d": round(_safe_float(merged.get("price_delta_1d")), 6),
            "price_delta_5d": round(_safe_float(merged.get("price_delta_5d")), 6),
        },
        "sentiment": {
            "news": round(_safe_float(merged.get("sentiment_news")), 4),
            "social": round(_safe_float(merged.get("sentiment_social")), 4),
            "divergence": merged["sentiment_divergence"],
        },
        "signal": explanation["signal"],
        "narrative": explanation["narrative"],
        "top_factors": explanation["top_factors"],
        "divergence": divergence,
    }


def build_news_feed(ticker: str, limit: int = 10) -> List[Dict]:
    rows = storage.filter_rows_for_ticker(storage.load_news_articles(limit=100), ticker)
    if not rows:
        return []

    feed = []
    for row in rows[:limit]:
        headline = str(row.get("headline", ""))
        score = row.get("sentiment_score")
        if score is None or score == "":
            summary = sentiment.sentiment_score(headline)
            score = summary["score"]
            label = summary["label"]
        else:
            score = round(_safe_float(score), 4)
            label = "positive" if score > 0.1 else "negative" if score < -0.1 else "neutral"
        feed.append(
            {
                "headline": headline,
                "source": row.get("source", ""),
                "published_at": row.get("published_at", ""),
                "url": row.get("url", ""),
                "sentiment": {"label": label, "score": round(_safe_float(score), 4)},
            }
        )
    return feed


def analyze_portfolio(holdings: List[Dict], user_subject: str) -> Dict:
    items = []
    total_market_value = 0.0
    signal_counts = {"BUY": 0, "HOLD": 0, "SELL": 0}

    for holding in holdings:
        ticker = holding["ticker"].upper()
        quantity = _safe_float(holding["quantity"], default=0.0)
        average_cost = _safe_float(holding.get("average_cost"), default=0.0)
        snapshot = build_signal_snapshot(ticker)
        close_price = snapshot["market"]["close"]
        market_value = round(close_price * quantity, 2)
        unrealized_pnl = round((close_price - average_cost) * quantity, 2) if average_cost else None
        signal_label = snapshot["signal"]["label"]
        signal_counts[signal_label] += 1
        total_market_value += market_value
        items.append(
            {
                "ticker": ticker,
                "quantity": quantity,
                "average_cost": average_cost if average_cost else None,
                "market_value": market_value,
                "unrealized_pnl": unrealized_pnl,
                "signal": snapshot["signal"],
                "divergence": snapshot["divergence"],
            }
        )

    risk_level = "low"
    if signal_counts["SELL"] > 0:
        risk_level = "high"
    elif signal_counts["HOLD"] >= max(1, len(items) // 2):
        risk_level = "medium"

    return {
        "user": user_subject,
        "portfolio_size": len(items),
        "total_market_value": round(total_market_value, 2),
        "signal_mix": signal_counts,
        "risk_level": risk_level,
        "holdings": items,
    }


def build_live_payload(ticker: str) -> Dict:
    signal_snapshot = build_signal_snapshot(ticker)
    return {
        "ticker": ticker.upper(),
        "type": "live_signal_snapshot",
        "as_of": signal_snapshot["as_of"],
        "market": signal_snapshot["market"],
        "signal": signal_snapshot["signal"],
        "divergence": signal_snapshot["divergence"],
        "sentiment": signal_snapshot["sentiment"],
    }
