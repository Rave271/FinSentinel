import os
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from typing import Dict, Iterable, List, Optional

from . import config  # noqa: F401  Loads repo .env before DATABASE_URL is read.

try:
    import psycopg2
except ImportError:  # pragma: no cover - exercised when postgres extras are unavailable
    psycopg2 = None


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


def _require_database() -> None:
    if not database_configured():
        raise RuntimeError("Database storage is required; set DATABASE_URL and install psycopg2")


def _iso(value):
    return value.isoformat() if value is not None else ""


def load_headlines(limit: int = 50) -> List[Dict]:
    _require_database()
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, headline, source, published_at, sentiment_score
                FROM headlines
                ORDER BY published_at DESC NULLS LAST, id DESC
                LIMIT %s
                """,
                (limit,),
            )
            rows = cursor.fetchall()
    return [
        {
            "id": row[0],
            "headline": row[1],
            "source": row[2] or "",
            "published_at": _iso(row[3]),
            "sentiment_score": float(row[4]) if row[4] is not None else None,
        }
        for row in rows
    ]


def load_news_articles(limit: int = 50) -> List[Dict]:
    _require_database()
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, title, source, published_at, url, sentiment_score
                FROM news_articles
                ORDER BY published_at DESC NULLS LAST, id DESC
                LIMIT %s
                """,
                (limit,),
            )
            rows = cursor.fetchall()
    return [
        {
            "id": row[0],
            "headline": row[1],
            "source": row[2] or "",
            "published_at": _iso(row[3]),
            "url": row[4] or "",
            "sentiment_score": float(row[5]) if row[5] is not None else None,
        }
        for row in rows
    ]


def load_price_quotes(limit: int = 50) -> List[Dict]:
    _require_database()
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT symbol, price, volume, timestamp
                FROM price_quotes
                ORDER BY timestamp DESC NULLS LAST, id DESC
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
            "timestamp": _iso(row[3]),
        }
        for row in rows
    ]


def insert_news_articles(rows: List[Dict]) -> int:
    _require_database()
    if not rows:
        return 0

    payload = []
    for row in rows:
        payload.append(
            (
                row.get("external_id"),
                row.get("headline") or row.get("title") or "",
                row.get("source"),
                row.get("url"),
                row.get("published_at") or row.get("publishedAt") or None,
                row.get("sentiment_score"),
            )
        )

    with get_connection() as connection:
        with connection:
            with connection.cursor() as cursor:
                cursor.executemany(
                    """
                    INSERT INTO news_articles (external_id, title, source, url, published_at, sentiment_score)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    payload,
                )
    return len(payload)


def insert_price_quote(symbol: str, price, volume, timestamp) -> None:
    _require_database()
    with get_connection() as connection:
        with connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO price_quotes (symbol, price, volume, timestamp)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (symbol, price, volume, timestamp),
                )


def create_user(email: str, password_hash: str, role: str = "user") -> Dict:
    _require_database()
    with get_connection() as connection:
        with connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO app_users (email, password_hash, role)
                    VALUES (%s, %s, %s)
                    RETURNING id, email, role, created_at
                    """,
                    (email, password_hash, role),
                )
                row = cursor.fetchone()
    return {
        "id": row[0],
        "email": row[1],
        "role": row[2],
        "created_at": _iso(row[3]),
    }


def get_user_by_email(email: str) -> Optional[Dict]:
    _require_database()
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, email, password_hash, role, created_at
                FROM app_users
                WHERE email = %s
                """,
                (email,),
            )
            row = cursor.fetchone()
    if row is None:
        return None
    return {
        "id": row[0],
        "email": row[1],
        "password_hash": row[2],
        "role": row[3],
        "created_at": _iso(row[4]),
    }


def create_session(user_id: int, token_hash: str, ttl_seconds: int) -> Dict:
    _require_database()
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)
    with get_connection() as connection:
        with connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO app_sessions (user_id, token_hash, expires_at)
                    VALUES (%s, %s, %s)
                    RETURNING id, user_id, expires_at, created_at
                    """,
                    (user_id, token_hash, expires_at),
                )
                row = cursor.fetchone()
    return {
        "id": row[0],
        "user_id": row[1],
        "expires_at": _iso(row[2]),
        "created_at": _iso(row[3]),
    }


def get_active_session(token_hash: str) -> Optional[Dict]:
    _require_database()
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    s.id,
                    s.user_id,
                    s.expires_at,
                    u.email,
                    u.role
                FROM app_sessions s
                JOIN app_users u ON u.id = s.user_id
                WHERE s.token_hash = %s
                    AND s.revoked_at IS NULL
                    AND s.expires_at > NOW()
                """,
                (token_hash,),
            )
            row = cursor.fetchone()
    if row is None:
        return None
    return {
        "session_id": row[0],
        "user_id": row[1],
        "expires_at": _iso(row[2]),
        "email": row[3],
        "role": row[4],
    }


def revoke_session(token_hash: str) -> bool:
    _require_database()
    with get_connection() as connection:
        with connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE app_sessions
                    SET revoked_at = NOW()
                    WHERE token_hash = %s AND revoked_at IS NULL
                    """,
                    (token_hash,),
                )
                return cursor.rowcount > 0


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
