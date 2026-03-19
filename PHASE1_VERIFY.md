# Phase 1 Redis Smoke Test

Run this after `docker-compose up` is bringing up Redis:

```bash
python3 - <<'PY'
import os
from redis import Redis
from backend.app.workers import social_worker

r = Redis.from_url(os.environ.get('REDIS_URL', 'redis://localhost:6379/0'))
print('PING', r.ping())
for ticker in social_worker.get_watchlist():
    social_worker.fetch_ticker_news(ticker, redis_client=r)
print('XLEN', r.xlen('social:stream'))
for entry_id, fields in r.xrange('social:stream', count=3):
    print(entry_id.decode(), {k.decode(): v.decode() for k, v in fields.items()})
PY
```
