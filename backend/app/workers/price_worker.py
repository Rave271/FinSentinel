#!/usr/bin/env python3
import os
import time
import csv
import traceback
from redis import Redis


REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
redis = Redis.from_url(REDIS_URL)

DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', '..', 'data', 'price_quotes.csv')


def read_prices():
    rows = []
    try:
        with open(DATA_PATH, newline='', encoding='utf-8') as f:
            sample = f.read(1024)
            f.seek(0)
            has_header = csv.Sniffer().has_header(sample) if sample.strip() else False
            if has_header:
                reader = csv.DictReader(f)
                for r in reader:
                    rows.append(r)
            else:
                reader = csv.reader(f)
                for raw in reader:
                    if not raw:
                        continue
                    rows.append(
                        {
                            'symbol': raw[0] if len(raw) > 0 else '',
                            'price': raw[1] if len(raw) > 1 else '',
                            'volume': raw[2] if len(raw) > 2 else '',
                            'timestamp': raw[3] if len(raw) > 3 else '',
                        }
                    )
    except FileNotFoundError:
        return []
    return rows


def push_price_event(row, redis_client=None):
    # Normalise fields and XADD to Redis stream
    client = redis_client or redis
    fields = {
        'symbol': row.get('symbol', ''),
        'price': row.get('price', ''),
        'volume': row.get('volume', ''),
        'timestamp': row.get('timestamp', ''),
    }
    client.xadd('stream:price', fields)


def main_loop(poll_interval=60):
    backoff = 1
    max_backoff = 300
    print('Price worker started, pushing price events into stream:price')
    while True:
        try:
            rows = read_prices()
            for r in rows:
                push_price_event(r)
            backoff = 1
        except KeyboardInterrupt:
            raise
        except Exception:
            print('Price worker exception — backing off', backoff)
            traceback.print_exc()
            time.sleep(backoff)
            backoff = min(backoff * 2, max_backoff)
            continue
        time.sleep(poll_interval)


if __name__ == '__main__':
    main_loop()
