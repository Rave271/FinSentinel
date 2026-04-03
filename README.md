# FinSentinel

Real-time market sentiment and risk intelligence for Indian retail investing.

FinSentinel combines live price signals, financial news, and social/news sentiment into a single explainable decision layer.  
The long-term goal is simple: move from reactive chart-watching to a system that can say what is moving, why it is moving, and whether that move is worth trusting.

## What It Is

- `PriceFeed` ingests live market data
- `NewsFeed` pulls finance headlines from NewsAPI
- `SocialFeed` pulls Google News RSS by ticker
- `FinBERT` scores text sentiment
- Redis streams act as the event backbone
- FastAPI serves the backend layer

## Where We Stand

Phase 1 is complete.

- project scaffold is in place
- local env and Docker setup exist
- Alpha Vantage and NewsAPI keys were verified live
- ingestion workers are built and tested
- Google News RSS replaced Reddit for social ingestion

Phase 2 is underway.

- FinBERT is integrated and running
- headline scoring is working
- EWMA sentiment smoothing is implemented
- worker pipelines now attach sentiment metadata to events
- fine-tuning on Financial PhraseBank is in progress

## Current Stack

- Backend: FastAPI
- NLP: `ProsusAI/finbert`
- Streams/Cache: Redis
- Data Sources: Alpha Vantage, NewsAPI, Google News RSS
- Frontend target: React + TypeScript
- Deployment target: Render + Vercel

## Repo Layout

```text
backend/       FastAPI app, workers, sentiment pipeline, training scripts
data/          Local sample and generated data files
migrations/    Database schema
frontend/      Frontend workspace
To-do.txt      Working project tracker
LLD_FinSentinel.pdf
```

## Local Run

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

Useful endpoints:

- `GET /api/health`
- `GET /api/headlines`
- `GET /api/news`
- `GET /api/signal/{ticker}`
- `GET /api/news/{ticker}`
- `GET /api/divergence/{ticker}`
- `POST /api/portfolio/analyze`
- `WS /ws/live/{ticker}`

## Supabase DB

Set `DATABASE_URL` in `.env` to your Supabase Postgres connection string, then run:

```bash
python3 -m pip install -r backend/requirements.txt
python3 backend/run_migrations.py
```

`GET /api/health` reports whether the database is configured and reachable.

## Deployment

The recommended hosted stack for this repo is:

- frontend on Vercel
- backend on Render
- Redis-compatible cache on Render Key Value
- Postgres on Supabase

### Required production environment variables

Backend:

- `DATABASE_URL`
- `REDIS_URL`
- `JWT_SECRET`
- `NEWS_API_KEY`
- `ALPHA_VANTAGE_KEY`

Frontend:

- `VITE_API_URL`

### Render backend

This repo now includes a root-level [render.yaml](/Users/raghavverma/Code%20and%20other%20shité/FinSentinel/render.yaml) blueprint for:

- a Docker-based web service named `finsentinel-api`
- a Render Key Value instance named `finsentinel-cache`

Deploy flow:

1. Push this repo to GitHub.
2. In Render, create a new Blueprint and point it at the repo.
3. During initial setup, provide `DATABASE_URL`, `NEWS_API_KEY`, and `ALPHA_VANTAGE_KEY`.
4. After the web service is live, verify `https://<your-render-url>/api/health`.

The backend Docker image reads `PORT` automatically, so the same image works both locally and on Render.

### Vercel frontend

Set the project root to `frontend/` and add:

```bash
VITE_API_URL=https://<your-render-url>
```

Then deploy. The SPA rewrite config lives in `frontend/vercel.json`.

### Post-deploy checks

1. Open the Vercel site.
2. Search `RELIANCE`.
3. Confirm the signal card loads.
4. Confirm charts render.
5. Confirm `/api/health` reports database connectivity.

## Notes

- `.env` is intentionally ignored and should never be committed
- generated local data files are ignored
- Redis live verification for Phase 1 is saved in `PHASE1_VERIFY.md`

## Status

This repository is no longer a scaffold.  
It is now the active build of the project: ingestion layer done, sentiment layer live, model training in motion.
