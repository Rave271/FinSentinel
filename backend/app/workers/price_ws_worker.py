#!/usr/bin/env python3
import os
import json
import time
import traceback
from redis import Redis

try:
    from websocket import WebSocketApp
except Exception:
    WebSocketApp = None


REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
redis = Redis.from_url(REDIS_URL)

WS_URL = os.environ.get("ALPHA_VANTAGE_WS")  # configurable websocket endpoint
FALLBACK_POLL_INTERVAL = int(os.environ.get("PRICE_POLL_INTERVAL", "60"))


def _push_price(fields: dict):
    # ensure all values are strings
    clean = {k: str(v) for k, v in fields.items() if v is not None}
    redis.xadd('stream:price', clean)


def _handle_message(msg_text: str):
    try:
        data = json.loads(msg_text)
    except Exception:
        # Not JSON, ignore
        return

    # attempt to extract common fields from various providers
    symbol = data.get('symbol') or data.get('s') or data.get('ticker')
    price = data.get('price') or data.get('p') or data.get('c') or data.get('last')
    volume = data.get('volume') or data.get('v')
    ts = data.get('timestamp') or data.get('t') or data.get('time')

    if not symbol and isinstance(data, dict):
        # some feeds wrap payload under 'data' or 'payload'
        for k in ('data', 'payload', 'message'):
            if k in data and isinstance(data[k], dict):
                return _handle_message(json.dumps(data[k]))

    if symbol and price is not None:
        _push_price({'symbol': symbol, 'price': price, 'volume': volume or '', 'timestamp': ts or ''})


class PriceWS:
    def __init__(self, url):
        self.url = url
        self.ws = None
        self.backoff = 1

    def on_message(self, ws, message):
        _handle_message(message)

    def on_error(self, ws, error):
        print('PriceWS error:', error)

    def on_close(self, ws, close_status_code, close_msg):
        print('PriceWS closed', close_status_code, close_msg)

    def on_open(self, ws):
        print('PriceWS connected')
        self.backoff = 1

    def run_forever(self):
        if WebSocketApp is None:
            print('websocket-client not available; cannot run WS worker')
            return
        while True:
            try:
                self.ws = WebSocketApp(self.url,
                                       on_message=self.on_message,
                                       on_error=self.on_error,
                                       on_close=self.on_close,
                                       on_open=self.on_open)
                self.ws.run_forever(ping_interval=30, ping_timeout=10)
            except KeyboardInterrupt:
                raise
            except Exception:
                print('PriceWS exception, reconnecting after backoff', self.backoff)
                traceback.print_exc()
                time.sleep(self.backoff)
                self.backoff = min(self.backoff * 2, 300)


def fallback_poller():
    # simple fallback that tails price_quotes.csv and pushes new rows
    import csv
    data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', '..', 'data', 'price_quotes.csv')
    last_seen = set()
    while True:
        try:
            if os.path.exists(data_path):
                with open(data_path, newline='', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for r in reader:
                        key = (r.get('symbol'), r.get('timestamp'), r.get('price'))
                        if key not in last_seen:
                            _push_price({'symbol': r.get('symbol', ''), 'price': r.get('price', ''), 'volume': r.get('volume', ''), 'timestamp': r.get('timestamp', '')})
                            last_seen.add(key)
        except Exception:
            print('PriceWS fallback poller error')
            traceback.print_exc()
        time.sleep(FALLBACK_POLL_INTERVAL)


def main():
    if WS_URL:
        print('Starting WebSocket price worker, connecting to', WS_URL)
        p = PriceWS(WS_URL)
        p.run_forever()
    else:
        print('ALPHA_VANTAGE_WS not set; running fallback poller')
        fallback_poller()


if __name__ == '__main__':
    main()
