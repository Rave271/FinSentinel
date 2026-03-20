#!/usr/bin/env python3
import os
import time
import traceback
from datetime import datetime, timezone
from urllib.parse import quote_plus

from redis import Redis
from app import sentiment

try:
    import feedparser
except Exception:
    feedparser = None

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
redis = Redis.from_url(REDIS_URL)

WATCHLIST = os.environ.get("SOCIAL_WATCHLIST", "RELIANCE,INFY,TCS")
POLL_INTERVAL = int(os.environ.get("SOCIAL_POLL_INTERVAL", "120"))
MAX_BACKOFF = int(os.environ.get("SOCIAL_MAX_BACKOFF", "300"))
STREAM_KEY = "social:stream"


def get_watchlist():
    return [ticker.strip().upper() for ticker in WATCHLIST.split(",") if ticker.strip()]


def build_feed_url(ticker):
    query = quote_plus(f"{ticker} stock")
    return (
        "https://news.google.com/rss/search"
        f"?q={query}&hl=en-IN&gl=IN&ceid=IN:en"
    )


def _entry_text(entry):
    title = (entry.get("title") or "").strip()
    summary = (entry.get("summary") or "").strip()
    parts = [part for part in (title, summary) if part]
    return " | ".join(parts)


def push_event(ticker, text, source, ts, sentiment_label, sentiment_score, redis_client=None):
    client = redis_client or redis
    fields = {
        "ticker": ticker,
        "text": text,
        "source": source,
        "sentiment_label": sentiment_label,
        "sentiment_score": sentiment_score,
        "ts": ts,
    }
    client.xadd(STREAM_KEY, fields)


def fetch_ticker_news(ticker, redis_client=None, parser=None):
    client = redis_client or redis
    parser_module = parser or feedparser
    if parser_module is None:
        raise RuntimeError("feedparser not installed")

    feed = parser_module.parse(build_feed_url(ticker))
    if getattr(feed, "bozo", 0):
        raise RuntimeError(f"feed parse failed for {ticker}")

    entries = list(getattr(feed, "entries", []))
    texts = []
    normalized_entries = []
    for entry in entries:
        text = _entry_text(entry)
        if not text:
            continue
        texts.append(text)
        normalized_entries.append(entry)

    scores = sentiment.score_texts(texts) if texts else []
    pushed_entries = []
    for entry, text, score in zip(normalized_entries, texts, scores):
        source = (entry.get("source", {}) or {}).get("title") or "google-news-rss"
        ts = (
            entry.get("published")
            or entry.get("updated")
            or datetime.now(timezone.utc).isoformat()
        )
        push_event(
            ticker=ticker,
            text=text,
            source=source,
            ts=ts,
            sentiment_label=score["sentiment_label"],
            sentiment_score=score["sentiment_score"],
            redis_client=client,
        )
        pushed_entries.append(
            {
                "ticker": ticker,
                "ts": ts,
                "sentiment_score": score["sentiment_score"],
            }
        )
    return pushed_entries


def cache_batch_sentiment(rows, redis_client=None):
    client = redis_client or redis
    by_ticker = {}
    for row in rows:
        ticker = row["ticker"]
        by_ticker.setdefault(ticker, {"scores": [], "timestamps": []})
        by_ticker[ticker]["scores"].append(float(row["sentiment_score"]))
        by_ticker[ticker]["timestamps"].append(row["ts"])

    for ticker, payload in by_ticker.items():
        ewma_score = sentiment.compute_ewma_score(
            ticker,
            payload["scores"],
            payload["timestamps"],
        )
        sentiment.cache_sentiment_score(ticker, "social", ewma_score, client)


def main_loop(poll_interval=POLL_INTERVAL):
    backoff = 1
    print("Social worker started with Google News RSS")
    while True:
        try:
            cycle_rows = []
            for ticker in get_watchlist():
                cycle_rows.extend(fetch_ticker_news(ticker))
            cache_batch_sentiment(cycle_rows)
            backoff = 1
            time.sleep(poll_interval)
        except KeyboardInterrupt:
            raise
        except Exception:
            print("Social worker exception — backing off", backoff)
            traceback.print_exc()
            time.sleep(backoff)
            backoff = min(backoff * 2, MAX_BACKOFF)


if __name__ == "__main__":
    main_loop()
