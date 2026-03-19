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

Useful endpoints:

- `GET /api/health`
- `GET /api/headlines`
- `GET /api/news`

## Notes

- `.env` is intentionally ignored and should never be committed
- generated local data files are ignored
- Redis live verification for Phase 1 is saved in `PHASE1_VERIFY.md`

## Status

This repository is no longer a scaffold.  
It is now the active build of the project: ingestion layer done, sentiment layer live, model training in motion.
