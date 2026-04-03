#!/usr/bin/env python3
import os
import glob
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv

try:
    import psycopg2
except ImportError:
    psycopg2 = None


REPO_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(REPO_ROOT / '.env', override=False)


def _redact_database_url(database_url):
    parsed = urlparse(database_url)
    host = parsed.hostname or "unknown-host"
    port = f":{parsed.port}" if parsed.port else ""
    path = parsed.path or ""
    user = parsed.username or "user"
    return f"{parsed.scheme}://{user}:***@{host}{port}{path}"

def run_migrations(database_url=None, migrations_path=None):
    database_url = database_url or os.environ.get('DATABASE_URL')
    migrations_path = migrations_path or os.path.join(os.path.dirname(__file__), '..', 'migrations')
    if not database_url:
        print('DATABASE_URL not set; skipping migrations')
        return 1
    if psycopg2 is None:
        print('psycopg2 is not installed; install backend requirements before running migrations')
        return 1

    sql_files = sorted(glob.glob(os.path.join(migrations_path, '*.sql')))
    if not sql_files:
        print('No migrations found in', migrations_path)
        return 0

    print('Running migrations against', _redact_database_url(database_url))
    conn = psycopg2.connect(database_url)
    try:
        with conn:
            with conn.cursor() as cur:
                for f in sql_files:
                    print('Applying', f)
                    with open(f, 'r', encoding='utf-8') as fh:
                        cur.execute(fh.read())
        print('Migrations applied successfully')
    finally:
        conn.close()
    return 0


if __name__ == '__main__':
    raise SystemExit(run_migrations())
