# FinSentinel — Phase 1 Minimal Scaffold

This repo contains a minimal FastAPI backend that reads sample headlines and returns a simple rule-based sentiment.

Quick start (Mac):

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload --port 8000
```

Endpoints:
- `GET /api/health` — health check
- `GET /api/headlines` — list sample headlines with sentiment

Next steps:
- Replace rule-based sentiment with FinBERT inference
- Add DB persistence and seed scripts
- Implement frontend dashboard
