#!/usr/bin/env python3
import json
import os
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

import pandas as pd

from app import sentiment

try:
    import feedparser
except Exception:
    feedparser = None

REPO_ROOT = Path(__file__).resolve().parent.parent
TRAINING_PATH = REPO_ROOT / "data" / "training_features.csv"
NEWS_DELAY_SECONDS = 1
PROGRESS_INTERVAL = 50
PRICE_DELTA_CLIP = 0.05
NEWS_PAGE_SIZE = 10
RECENT_BACKFILL_ROWS = 30


def load_env_file(path):
    env = {}
    try:
        with open(path, "r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                env[key.strip()] = value.strip()
    except FileNotFoundError:
        pass
    return env


def load_api_keys():
    env = load_env_file(REPO_ROOT / ".env")
    return {
        "news_api_key": env.get("NEWS_API_KEY") or os.environ.get("NEWS_API_KEY", ""),
    }


def build_newsapi_url(ticker, date_value, api_key):
    start = date_value.strftime("%Y-%m-%d")
    end = (date_value + timedelta(days=1)).strftime("%Y-%m-%d")
    params = {
        "q": f"{ticker} stock",
        "from": start,
        "to": end,
        "sortBy": "publishedAt",
        "language": "en",
        "pageSize": NEWS_PAGE_SIZE,
        "apiKey": api_key,
    }
    return "https://newsapi.org/v2/everything?" + urllib.parse.urlencode(params)


def fetch_newsapi_texts(ticker, date_value, api_key):
    if not api_key:
        return []

    url = build_newsapi_url(ticker, date_value, api_key)
    with urllib.request.urlopen(url, timeout=30) as response:
        payload = json.load(response)

    if payload.get("status") != "ok":
        return []

    articles = payload.get("articles", [])
    texts = []
    for article in articles:
        title = (article.get("title") or "").strip()
        description = (article.get("description") or "").strip()
        parts = [part for part in (title, description) if part]
        if parts:
            texts.append(" | ".join(parts))
    return texts


def build_google_news_feed_url(ticker, date_value):
    start = date_value.strftime("%Y-%m-%d")
    end = (date_value + timedelta(days=1)).strftime("%Y-%m-%d")
    query = urllib.parse.quote_plus(f"{ticker} stock after:{start} before:{end}")
    return (
        "https://news.google.com/rss/search"
        f"?q={query}&hl=en-IN&gl=IN&ceid=IN:en"
    )


def parse_entry_datetime(entry):
    for key in ("published", "updated"):
        raw = entry.get(key)
        if not raw:
            continue
        try:
            dt = parsedate_to_datetime(raw)
        except (TypeError, ValueError):
            continue
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    return None


def fetch_google_news_texts(ticker, date_value):
    if feedparser is None:
        return []

    start = datetime.combine(date_value.date(), datetime.min.time(), tzinfo=timezone.utc)
    end = start + timedelta(days=1)
    feed = feedparser.parse(build_google_news_feed_url(ticker, date_value))
    if getattr(feed, "bozo", 0):
        return []

    texts = []
    for entry in getattr(feed, "entries", []):
        published_at = parse_entry_datetime(entry)
        if published_at is not None and not (start <= published_at < end):
            continue

        title = (entry.get("title") or "").strip()
        summary = (entry.get("summary") or "").strip()
        parts = [part for part in (title, summary) if part]
        if parts:
            texts.append(" | ".join(parts))
    return texts


def mean_sentiment_score(texts):
    if not texts:
        return 0.0
    scores = sentiment.score_texts(texts)
    if not scores:
        return 0.0
    return round(
        sum(float(item["sentiment_score"]) for item in scores) / len(scores),
        4,
    )


def normalize_price_delta(price_delta_1d):
    clipped = max(-PRICE_DELTA_CLIP, min(PRICE_DELTA_CLIP, float(price_delta_1d)))
    return round(clipped / PRICE_DELTA_CLIP, 4)


def main():
    keys = load_api_keys()
    if not TRAINING_PATH.exists():
        raise FileNotFoundError(f"Missing training features file: {TRAINING_PATH}")

    df = pd.read_csv(TRAINING_PATH)
    df["date"] = pd.to_datetime(df["date"])
    df["sentiment_news"] = 0.0
    df["sentiment_social"] = 0.0

    total_rows = len(df)
    smoke_test_count = min(RECENT_BACKFILL_ROWS, total_rows)
    recent_indices = df.tail(smoke_test_count).index.tolist()
    print(f"running sentiment smoke test for the most recent {smoke_test_count} of {total_rows} rows")

    for position, index in enumerate(recent_indices, start=1):
        row = df.loc[index]
        ticker = str(row["ticker"]).upper()
        date_value = row["date"].to_pydatetime()

        try:
            news_texts = fetch_newsapi_texts(ticker, date_value, keys["news_api_key"])
        except Exception:
            news_texts = []
        news_score = mean_sentiment_score(news_texts)
        df.at[index, "sentiment_news"] = news_score

        try:
            social_texts = fetch_google_news_texts(ticker, date_value)
        except Exception:
            social_texts = []
        social_score = mean_sentiment_score(social_texts)
        df.at[index, "sentiment_social"] = social_score

        price_delta_normalized = normalize_price_delta(row["price_delta_1d"])
        divergence = abs(news_score - price_delta_normalized)
        df.at[index, "sentiment_divergence"] = round(divergence, 4)

        if position % PROGRESS_INTERVAL == 0 or position == smoke_test_count:
            print(f"processed {position}/{smoke_test_count} smoke-test rows")

        time.sleep(NEWS_DELAY_SECONDS)

    for index in df.index.difference(recent_indices):
        price_delta_normalized = normalize_price_delta(df.at[index, "price_delta_1d"])
        df.at[index, "sentiment_divergence"] = round(abs(price_delta_normalized), 4)

    df["date"] = df["date"].dt.strftime("%Y-%m-%d")
    df.to_csv(TRAINING_PATH, index=False)

    recent_mask = df.index.isin(recent_indices)
    placeholder_mask = ~recent_mask
    mean_abs_news_recent = round(df.loc[recent_mask, "sentiment_news"].abs().mean(), 4)
    mean_abs_news_placeholder = round(df.loc[placeholder_mask, "sentiment_news"].abs().mean(), 4)
    mean_abs_news = round(df["sentiment_news"].abs().mean(), 4)
    mean_abs_social = round(df["sentiment_social"].abs().mean(), 4)
    print(f"saved backfilled data to {TRAINING_PATH}")
    print(f"recent_rows_with_live_backfill={smoke_test_count}")
    print(f"placeholder_rows={int(placeholder_mask.sum())}")
    print(f"mean_abs_sentiment_news_recent={mean_abs_news_recent}")
    print(f"mean_abs_sentiment_news_placeholder={mean_abs_news_placeholder}")
    print(f"mean_abs_sentiment_news={mean_abs_news}")
    print(f"mean_abs_sentiment_social={mean_abs_social}")


if __name__ == "__main__":
    main()
