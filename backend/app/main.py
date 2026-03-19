from fastapi import FastAPI
from fastapi.responses import JSONResponse
import os
import pandas as pd
from .sentiment import sentiment_score

app = FastAPI(title="FinSentinel - Minimal API")

ROOT = os.path.dirname(os.path.dirname(__file__))
SAMPLE_PATH = os.path.normpath(os.path.join(ROOT, '..', 'data', 'sample_headlines.csv'))
NEWS_PATH = os.path.normpath(os.path.join(ROOT, '..', 'data', 'news_headlines.csv'))


def _load_csv(path, default_rows=None):
    if os.path.exists(path):
        try:
            return pd.read_csv(path)
        except Exception:
            return pd.DataFrame(default_rows or [])
    else:
        return pd.DataFrame(default_rows or [])


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/headlines")
def list_headlines():
    df = _load_csv(SAMPLE_PATH, default_rows=[{"id": 1, "headline": "No sample data found"}])
    records = df.to_dict(orient="records")
    for r in records:
        r["sentiment"] = sentiment_score(r.get("headline", ""))
    return JSONResponse(content=records)


@app.get("/api/news")
def list_news():
    df = _load_csv(NEWS_PATH, default_rows=[])
    records = df.to_dict(orient="records")
    for r in records:
        # some CSV rows include quotes — ensure headline is a string
        headline = r.get("headline") or ""
        r["sentiment"] = sentiment_score(headline)
    return JSONResponse(content=records)
