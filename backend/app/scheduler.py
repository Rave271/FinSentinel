import asyncio
import os
from typing import List

from . import explainability
from .universe import NIFTY50_SYMBOLS

try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
except ImportError:  # pragma: no cover - exercised when dependency is missing
    AsyncIOScheduler = None


ENABLE_BACKGROUND_WORKERS = os.environ.get("ENABLE_BACKGROUND_WORKERS", "0") == "1"
WATCHLIST = os.environ.get("SIGNAL_WATCHLIST", os.environ.get("SOCIAL_WATCHLIST", ",".join(NIFTY50_SYMBOLS)))


def get_watchlist() -> List[str]:
    return [ticker.strip().upper() for ticker in WATCHLIST.split(",") if ticker.strip()]


async def warm_explanations_job():
    for ticker in get_watchlist():
        try:
            feature_row = explainability.load_latest_training_row(ticker)
            await explainability.precompute_signal_explanation(ticker, feature_row)
        except Exception:
            continue


def poll_news_once():
    from .workers import news_worker

    rows = news_worker.read_articles()
    if not rows:
        return
    enriched = news_worker.enrich_articles_with_sentiment(rows)
    news_worker.cache_batch_sentiment(enriched)


def poll_social_once():
    from .workers import social_worker

    cycle_rows = []
    for ticker in social_worker.get_watchlist():
        cycle_rows.extend(social_worker.fetch_ticker_news(ticker))
    if cycle_rows:
        social_worker.cache_batch_sentiment(cycle_rows)


def build_scheduler():
    if AsyncIOScheduler is None:
        return None

    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(
        lambda: asyncio.create_task(warm_explanations_job()),
        "interval",
        minutes=5,
        id="warm-explanations",
        replace_existing=True,
    )
    if ENABLE_BACKGROUND_WORKERS:
        scheduler.add_job(
            poll_news_once,
            "interval",
            minutes=2,
            id="poll-news-once",
            replace_existing=True,
        )
        scheduler.add_job(
            poll_social_once,
            "interval",
            minutes=3,
            id="poll-social-once",
            replace_existing=True,
        )
    return scheduler
