import asyncio
import os
from contextlib import asynccontextmanager

import pandas as pd
from fastapi import BackgroundTasks, FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from . import config  # noqa: F401  Ensures repo .env is loaded before settings are read.
from . import explainability, storage
from .market import analyze_portfolio, build_divergence_snapshot, build_live_payload, build_news_feed, build_signal_snapshot
from .scheduler import build_scheduler
from .security import InMemoryRateLimiter, create_access_token, decode_access_token, extract_bearer_token
from .sentiment import sentiment_score


ROOT = os.path.dirname(os.path.dirname(__file__))
SAMPLE_PATH = os.path.normpath(os.path.join(ROOT, "..", "data", "sample_headlines.csv"))
NEWS_PATH = os.path.normpath(os.path.join(ROOT, "..", "data", "news_headlines.csv"))
WS_PUSH_INTERVAL_SECONDS = float(os.environ.get("WS_PUSH_INTERVAL_SECONDS", "60"))
ALLOW_DEV_AUTH_TOKENS = os.environ.get("ALLOW_DEV_AUTH_TOKENS", "1") == "1"

rate_limiter = InMemoryRateLimiter()
scheduler = build_scheduler()


def _load_csv(path, default_rows=None):
    if os.path.exists(path):
        try:
            return pd.read_csv(path)
        except Exception:
            return pd.DataFrame(default_rows or [])
    else:
        return pd.DataFrame(default_rows or [])


def _requires_auth(request: Request) -> bool:
    return request.url.path == "/api/portfolio/analyze" and request.method.upper() == "POST"


def _current_subject(request: Request) -> str:
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return str(user["sub"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    if scheduler is not None and not scheduler.running:
        scheduler.start()
    try:
        yield
    finally:
        if scheduler is not None and scheduler.running:
            scheduler.shutdown(wait=False)


app = FastAPI(title="FinSentinel API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def auth_and_rate_limit_middleware(request: Request, call_next):
    if request.url.path.startswith("/api/") and request.url.path != "/api/health":
        client_host = request.client.host if request.client else "anonymous"
        key = f"{client_host}:{request.url.path}"
        allowed, retry_after = rate_limiter.check(key)
        if not allowed:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"},
                headers={"Retry-After": str(retry_after)},
            )

    request.state.user = None
    token = extract_bearer_token(request.headers.get("Authorization"))
    if token:
        try:
            request.state.user = decode_access_token(token)
        except ValueError:
            if _requires_auth(request):
                return JSONResponse(status_code=401, content={"detail": "Invalid bearer token"})
    elif _requires_auth(request):
        return JSONResponse(status_code=401, content={"detail": "Authentication required"})

    return await call_next(request)


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "cors": True,
        "rate_limit": {
            "max_requests": rate_limiter.max_requests,
            "window_seconds": rate_limiter.window_seconds,
        },
        "scheduler": {
            "enabled": scheduler is not None,
            "running": bool(scheduler.running) if scheduler is not None else False,
        },
        "database": storage.database_health(),
    }


@app.get("/api/headlines")
def list_headlines():
    df = _load_csv(SAMPLE_PATH, default_rows=[{"id": 1, "headline": "No sample data found"}])
    records = df.to_dict(orient="records")
    for record in records:
        record["sentiment"] = sentiment_score(record.get("headline", ""))
    return JSONResponse(content=records)


@app.get("/api/news")
def list_news():
    records = storage.load_news_articles(limit=50)
    for record in records:
        headline = record.get("headline") or ""
        record["sentiment"] = sentiment_score(headline)
    return JSONResponse(content=records)


@app.get("/api/auth/dev-token")
def issue_dev_token(subject: str = "demo-user", role: str = "demo"):
    if not ALLOW_DEV_AUTH_TOKENS:
        raise HTTPException(status_code=404, detail="Developer auth tokens are disabled")
    return {"access_token": create_access_token(subject=subject, role=role), "token_type": "bearer"}


@app.get("/api/signal/{ticker}")
def get_signal(ticker: str):
    try:
        payload = build_signal_snapshot(ticker)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return JSONResponse(content=payload)


@app.get("/api/news/{ticker}")
def get_ticker_news(ticker: str, limit: int = 10):
    return JSONResponse(content={"ticker": ticker.upper(), "items": build_news_feed(ticker, limit=limit)})


@app.get("/api/divergence/{ticker}")
def get_divergence(ticker: str):
    try:
        payload = build_divergence_snapshot(ticker)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return JSONResponse(content=payload)


@app.post("/api/portfolio/analyze")
async def portfolio_analyze(request: Request):
    payload = await request.json()
    holdings = payload.get("holdings", [])
    if not isinstance(holdings, list) or not holdings:
        raise HTTPException(status_code=422, detail="holdings must be a non-empty list")

    normalized = []
    for item in holdings:
        ticker = str(item.get("ticker", "")).strip().upper()
        if not ticker:
            raise HTTPException(status_code=422, detail="each holding requires a ticker")
        normalized.append(
            {
                "ticker": ticker,
                "quantity": item.get("quantity", 0),
                "average_cost": item.get("average_cost"),
            }
        )

    subject = _current_subject(request)
    try:
        result = analyze_portfolio(normalized, user_subject=subject)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return JSONResponse(content=result)


@app.get("/api/explain/{ticker}")
def explain_signal(ticker: str):
    cached = explainability.get_cached_signal_explanation(ticker)
    if cached is not None:
        cached["cache_status"] = "hit"
        return JSONResponse(content=cached)

    try:
        feature_row = explainability.load_latest_training_row(ticker)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    explanation = explainability.build_signal_explanation(ticker, feature_row)
    explainability.cache_signal_explanation(ticker, explanation)
    explanation["cache_status"] = "miss"
    return JSONResponse(content=explanation)


@app.post("/api/explain/{ticker}/precompute")
def precompute_explanation(ticker: str, background_tasks: BackgroundTasks):
    try:
        feature_row = explainability.load_latest_training_row(ticker)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    background_tasks.add_task(explainability.precompute_signal_explanation, ticker, feature_row)
    return {"status": "queued", "ticker": ticker.upper()}


@app.websocket("/ws/live/{ticker}")
async def live_signal_stream(websocket: WebSocket, ticker: str):
    await websocket.accept()
    try:
        while True:
            try:
                payload = build_live_payload(ticker)
            except KeyError:
                await websocket.send_json({"error": f"Ticker {ticker.upper()} not found"})
                break
            await websocket.send_json(payload)
            await asyncio.sleep(WS_PUSH_INTERVAL_SECONDS)
    except WebSocketDisconnect:
        return
