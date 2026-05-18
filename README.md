# FinSentinel

FinSentinel is a full-stack market sentiment and risk intelligence platform for Indian equities. It combines price action, news flow, and NLP-driven sentiment into an explainable signal layer that helps users understand not just what moved, but why it moved and how confident the system is in the move.

This repository is structured like a portfolio-ready product, not a demo. It includes live data ingestion, model scoring, backend APIs, authentication, background jobs, database persistence, and a React frontend for visualization.

## Resume Snapshot

If you need a short description for applications or interviews:

FinSentinel is an AI-assisted stock intelligence platform built with FastAPI, React, Redis, PostgreSQL, and FinBERT. It ingests live market/news data, scores sentiment, computes explainable trading signals, and exposes the result through a production-style web app and API.

## What It Does

- Pulls live market data for Indian equities through price and news workers
- Scores news and headline sentiment with FinBERT
- Combines price momentum, volume, and sentiment features into a signal layer
- Surfaces ticker-level views with explanations and charting in the frontend
- Supports authentication, sessions, and rate limiting in the API layer
- Uses background jobs and caches so the system can operate continuously

## Key Capabilities

- Multi-source ingestion: Alpha Vantage, NewsAPI, and Google News RSS
- NLP pipeline: FinBERT-based sentiment scoring and smoothing
- Explainability: generated signal explanations for ticker-level decisions
- Auth system: register, login, guest access, and session cookies
- Production safeguards: CORS, API rate limiting, and health checks
- Deployment-ready: Render backend, Vercel frontend, Supabase Postgres

## Architecture

```text
Market/news sources -> backend workers -> Redis cache / Postgres -> FastAPI API -> React frontend
							  |                                    |
							  +-> sentiment scoring / explanations  +-> auth, rate limiting, health checks
```

The backend is the control plane. Workers fetch and enrich data, the storage layer persists state, Redis keeps live sentiment accessible, and the frontend consumes the API for charts, cards, and ticker views.

## Tech Stack

- Backend: FastAPI, Python
- NLP: ProsusAI/FinBERT
- Data/Cache: Redis, PostgreSQL, Supabase
- Frontend: React, TypeScript, Vite, Recharts
- Deployment: Render, Vercel
- Model training: XGBoost for signal classification

## Repository Layout

```text
backend/       API, workers, storage, sentiment, explainability, training scripts
frontend/      React + TypeScript web app
data/          Sample, generated, and historical market data
migrations/    SQL schema for local or hosted Postgres
docs/          Reference notes and supporting documentation
```

## Local Setup

Backend:

```bash
python3 -m pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload --port 8000
```

Frontend:

```bash
cd frontend
npm install
VITE_API_URL=http://localhost:8000 npm run dev
```

Docker-based local stack:

```bash
docker compose up --build
```

## Environment Variables

Backend:

- `DATABASE_URL`
- `REDIS_URL`
- `JWT_SECRET`
- `NEWS_API_KEY`
- `ALPHA_VANTAGE_KEY`
- `FRONTEND_URL`
- `CORS_ORIGINS`
- `ENABLE_BACKGROUND_WORKERS`
- `ALLOW_DEV_AUTH_TOKENS`

Frontend:

- `VITE_API_URL`

Production cookie settings:

- `SESSION_COOKIE_SECURE=1`
- `SESSION_COOKIE_SAMESITE=none`

## API Surface

Common endpoints:

- `GET /api/health`
- `GET /api/headlines`
- `GET /api/news`
- `GET /api/signal/{ticker}`
- `GET /api/news/{ticker}`
- `GET /api/divergence/{ticker}`
- `POST /api/portfolio/analyze`
- `WS /ws/live/{ticker}`

Auth endpoints:

- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/auth/guest`
- `GET /api/auth/dev-token`

## Database

The app supports PostgreSQL via `DATABASE_URL`. After configuring the connection string, run the migration script:

```bash
python3 backend/run_migrations.py
```

The health endpoint reports whether the database is configured and reachable.

## Deployment

Recommended hosted setup:

- Frontend on Vercel
- Backend on Render
- Postgres on Supabase
- Redis-compatible cache on Render Key Value

This repo includes a root-level [render.yaml](render.yaml) blueprint for the backend service and cache instance.

Render deploy flow:

1. Push the repo to GitHub.
2. Create a Render Blueprint and point it at the repository.
3. Set `DATABASE_URL`, `NEWS_API_KEY`, and `ALPHA_VANTAGE_KEY`.
4. Confirm `https://<your-render-url>/api/health` returns `status: ok`.

Vercel deploy flow:

1. Set the project root to `frontend/`.
2. Set `VITE_API_URL` to the Render backend URL.
3. Deploy using the SPA rewrite rules in `frontend/vercel.json`.

## Current Status

- Phase 1: completed scaffold, verified live API keys, built workers, and validated ingestion
- Phase 2: FinBERT integration, headline scoring, sentiment smoothing, and explanation precomputation are in place
- Training: XGBoost signal model training is included in the repo and uses engineered price plus sentiment features

## Notes

- `.env` is intentionally ignored and should not be committed
- generated local data files are ignored
- `PHASE1_VERIFY.md` contains the Phase 1 verification notes

## Why This Project Reads Well On A Resume

- It demonstrates end-to-end product thinking, not just a notebook or model script
- It shows a realistic full-stack architecture with backend, frontend, persistence, and deployment
- It includes AI/ML work that is integrated into an actual user-facing system
- It has practical engineering concerns covered: auth, rate limiting, health checks, workers, and environment management
