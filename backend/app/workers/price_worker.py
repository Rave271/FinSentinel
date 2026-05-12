#!/usr/bin/env python3
import os
import time
import traceback
from redis import Redis

from app import storage


REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
redis = Redis.from_url(REDIS_URL)

def read_prices():
    try:
        return storage.load_price_quotes(limit=500)
    except Exception:
        return []


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
