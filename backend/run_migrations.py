#!/usr/bin/env python3
import os
import glob
import psycopg2

def run_migrations(database_url=None, migrations_path=None):
    database_url = database_url or os.environ.get('DATABASE_URL')
    migrations_path = migrations_path or os.path.join(os.path.dirname(__file__), '..', '..', 'migrations')
    if not database_url:
        print('DATABASE_URL not set; skipping migrations')
        return 1

    sql_files = sorted(glob.glob(os.path.join(migrations_path, '*.sql')))
    if not sql_files:
        print('No migrations found in', migrations_path)
        return 0

    print('Running migrations against', database_url)
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
