#!/usr/bin/env python3
import os
import time
import csv
import traceback
from datetime import datetime, timezone
from redis import Redis

from app import sentiment

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
redis = Redis.from_url(REDIS_URL)

DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', '..', 'data', 'news_headlines.csv')
STREAM_KEY = "news:stream"
WATCHLIST = os.environ.get("NEWS_WATCHLIST", os.environ.get("SOCIAL_WATCHLIST", "RELIANCE,INFY,TCS"))


def read_articles():
    rows = []
    try:
        with open(DATA_PATH, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for r in reader:
                rows.append(r)
    except FileNotFoundError:
        return []
    return rows


def get_watchlist():
    return [ticker.strip().upper() for ticker in WATCHLIST.split(",") if ticker.strip()]


def infer_ticker(article, watchlist=None):
    watchlist = watchlist or get_watchlist()
    if article.get("ticker"):
        return str(article["ticker"]).upper()

    haystack = " ".join(
        [
            str(article.get("headline", "")),
            str(article.get("source", "")),
            str(article.get("url", "")),
        ]
    ).upper()
    for ticker in watchlist:
        if ticker in haystack:
            return ticker
    return "MARKET"


def enrich_articles_with_sentiment(rows):
    headlines = [row.get("headline") or "" for row in rows]
    sentiment_rows = sentiment.score_texts(headlines) if headlines else []
    enriched = []
    now = datetime.now(timezone.utc).isoformat()
    for row, score in zip(rows, sentiment_rows):
        enriched_row = dict(row)
        enriched_row["ticker"] = infer_ticker(enriched_row)
        enriched_row["published_at"] = row.get("published_at") or row.get("publishedAt") or ""
        enriched_row["sentiment_label"] = score["sentiment_label"]
        enriched_row["sentiment_score"] = score["sentiment_score"]
        enriched_row["ts"] = now
        enriched.append(enriched_row)
    return enriched


def push_article(a, redis_client=None):
    client = redis_client or redis
    url = a.get('url') or a.get('headline')
    if not url:
        return
    added = client.sadd('news:seen', url)
    if added:
        fields = {
            'ticker': a.get('ticker', 'MARKET'),
            'headline': a.get('headline', ''),
            'source': a.get('source', ''),
            'published_at': a.get('published_at') or a.get('publishedAt', ''),
            'sentiment_label': a.get('sentiment_label', 'neutral'),
            'sentiment_score': a.get('sentiment_score', 0.0),
            'ts': a.get('ts', ''),
        }
        client.xadd(STREAM_KEY, fields)


def main_loop(poll_interval=90):
    backoff = 1
    max_backoff = 300
    print('News worker started, polling news and writing to news:stream')
    while True:
        try:
            rows = read_articles()
            for a in enrich_articles_with_sentiment(rows):
                push_article(a)
            backoff = 1
        except KeyboardInterrupt:
            raise
        except Exception:
            print('News worker exception — backing off', backoff)
            traceback.print_exc()
            time.sleep(backoff)
            backoff = min(backoff * 2, max_backoff)
            continue
        time.sleep(poll_interval)


if __name__ == '__main__':
    main_loop()
