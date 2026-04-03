import csv
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, Iterable, List

from . import config  # noqa: F401  Loads repo .env before DATABASE_URL is read.

try:
    import psycopg2
except ImportError:  # pragma: no cover - exercised when postgres extras are unavailable
    psycopg2 = None


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
NEWS_PATH = REPO_ROOT / "data" / "news_headlines.csv"
PRICE_PATH = REPO_ROOT / "data" / "price_quotes.csv"
DATABASE_URL = os.environ.get("DATABASE_URL", "")


def database_configured() -> bool:
    return bool(DATABASE_URL and psycopg2 is not None)


@contextmanager
def get_connection():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not configured")
    if psycopg2 is None:
        raise RuntimeError("psycopg2 is not installed")
    connection = psycopg2.connect(DATABASE_URL)
    try:
        yield connection
    finally:
        connection.close()


def database_health() -> Dict:
    if not DATABASE_URL:
        return {"configured": False, "healthy": False}
    if psycopg2 is None:
        return {"configured": True, "healthy": False, "error": "psycopg2 is not installed"}
    try:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        return {"configured": True, "healthy": True}
    except Exception as exc:
        return {"configured": True, "healthy": False, "error": str(exc)}


def _normalize_csv_rows(path: Path, field_names: List[str]) -> List[Dict]:
    if not path.exists():
        return []

    with open(path, newline="", encoding="utf-8") as handle:
        rows = list(csv.reader(handle))

    if not rows:
        return []

    first_row = [cell.strip().lower() for cell in rows[0]]
    normalized_fields = [name.lower() for name in field_names]
    start_index = 1 if first_row[: len(normalized_fields)] == normalized_fields else 0

    normalized = []
    for raw_row in rows[start_index:]:
        if not any(cell.strip() for cell in raw_row):
            continue
        record = {field: (raw_row[index].strip() if index < len(raw_row) else "") for index, field in enumerate(field_names)}
        normalized.append(record)
    return normalized


def load_news_articles(limit: int = 50) -> List[Dict]:
    if database_configured():
        try:
            with get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT id, title, source, published_at, url, sentiment_score
                        FROM news_articles
                        ORDER BY published_at DESC NULLS LAST
                        LIMIT %s
                        """,
                        (limit,),
                    )
                    rows = cursor.fetchall()
            return [
                {
                    "id": row[0],
                    "headline": row[1],
                    "source": row[2],
                    "published_at": row[3].isoformat() if row[3] else "",
                    "url": row[4],
                    "sentiment_score": float(row[5]) if row[5] is not None else None,
                }
                for row in rows
            ]
        except Exception:
            pass

    return _normalize_csv_rows(NEWS_PATH, ["id", "headline", "source", "published_at", "url"])[:limit]


def load_price_quotes(limit: int = 50) -> List[Dict]:
    if database_configured():
        try:
            with get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT symbol, price, volume, timestamp
                        FROM price_quotes
                        ORDER BY timestamp DESC NULLS LAST
                        LIMIT %s
                        """,
                        (limit,),
                    )
                    rows = cursor.fetchall()
            return [
                {
                    "symbol": row[0],
                    "price": float(row[1]) if row[1] is not None else None,
                    "volume": int(row[2]) if row[2] is not None else None,
                    "timestamp": row[3].isoformat() if row[3] else "",
                }
                for row in rows
            ]
        except Exception:
            pass

    return _normalize_csv_rows(PRICE_PATH, ["symbol", "price", "volume", "timestamp"])[:limit]


def filter_rows_for_ticker(rows: Iterable[Dict], ticker: str) -> List[Dict]:
    needle = ticker.upper()
    filtered = []
    for row in rows:
        haystack = " ".join(
            [
                str(row.get("ticker", "")),
                str(row.get("headline", "")),
                str(row.get("source", "")),
                str(row.get("url", "")),
                str(row.get("symbol", "")),
            ]
        ).upper()
        if needle in haystack:
            filtered.append(dict(row))
    return filtered
