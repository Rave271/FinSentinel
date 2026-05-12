import asyncio
import os

from contextlib import asynccontextmanager

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request, Response, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from pydantic import BaseModel

from . import config  # noqa: F401  Ensures repo .env is loaded before settings are read.
from . import explainability, storage
from .market import analyze_portfolio, build_divergence_snapshot, build_live_payload, build_news_feed, build_signal_snapshot
from .scheduler import build_scheduler
from .security import (
    InMemoryRateLimiter,
    create_access_token,
    decode_access_token,
    extract_bearer_token,
    generate_session_token,
    hash_password,
    hash_session_token,
    verify_password,
)
from .sentiment import sentiment_score


WS_PUSH_INTERVAL_SECONDS = float(os.environ.get("WS_PUSH_INTERVAL_SECONDS", "60"))
ALLOW_DEV_AUTH_TOKENS = os.environ.get("ALLOW_DEV_AUTH_TOKENS", "1") == "1"
FRONTEND_URL = os.environ.get("FRONTEND_URL", "").strip()
_configured_cors_origins = [
    origin.strip()
    for origin in os.environ.get("CORS_ORIGINS", "").split(",")
    if origin.strip()
]
CORS_ORIGINS = list(
    dict.fromkeys(
        _configured_cors_origins
        + ([FRONTEND_URL] if FRONTEND_URL else [])
        + [
            "http://localhost:3000",
            "http://localhost:4173",
            "http://localhost:5173",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:4173",
            "http://127.0.0.1:5173",
        ]
    )
)
SESSION_COOKIE_NAME = os.environ.get("SESSION_COOKIE_NAME", "finsentinel_session")
SESSION_TTL_SECONDS = int(os.environ.get("SESSION_TTL_SECONDS", "86400"))
SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "0") == "1"
SESSION_COOKIE_SAMESITE = os.environ.get("SESSION_COOKIE_SAMESITE", "lax").strip().lower()

rate_limiter = InMemoryRateLimiter()
scheduler = build_scheduler()


class RegisterPayload(BaseModel):
    email: str
    password: str


class LoginPayload(BaseModel):
    email: str
    password: str


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
    allow_origins=CORS_ORIGINS,
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
    else:
        session_token = request.cookies.get(SESSION_COOKIE_NAME)
        if session_token:
            try:
                session = storage.get_active_session(hash_session_token(session_token))
            except Exception:
                session = None
            if session is not None:
                request.state.user = {
                    "sub": session["email"],
                    "role": session["role"],
                    "user_id": session["user_id"],
                    "auth_type": "session",
                }

    if _requires_auth(request) and request.state.user is None:
        return JSONResponse(status_code=401, content={"detail": "Authentication required"})

    return await call_next(request)


@app.get("/", include_in_schema=False)
def root():
    if FRONTEND_URL:
        return RedirectResponse(url=FRONTEND_URL, status_code=307)
    return HTMLResponse(
        content=(
            "<html><head><title>FinSentinel API</title></head>"
            "<body style='font-family: sans-serif; margin: 2rem;'>"
            "<h1>FinSentinel API is running</h1>"
            "<p>This service only hosts backend APIs.</p>"
            "<p>Use <a href='/api/health'>/api/health</a> for health checks or "
            "<a href='/docs'>/docs</a> for API docs.</p>"
            "<p>Set FRONTEND_URL to redirect this root URL to your web app.</p>"
            "</body></html>"
        )
    )


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return Response(status_code=204)


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
    records = storage.load_headlines(limit=50)
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


@app.post("/api/auth/guest")
def guest_login():
    guest_email = "guest@finsentinel.local"
    guest_user = storage.get_user_by_email(guest_email)
    if guest_user is None:
      guest_user = storage.create_user(email=guest_email, password_hash=hash_password(generate_session_token()), role="guest")

    raw_token = generate_session_token()
    storage.create_session(user_id=guest_user["id"], token_hash=hash_session_token(raw_token), ttl_seconds=SESSION_TTL_SECONDS)

    response = JSONResponse(content={"id": guest_user["id"], "email": guest_user["email"], "role": guest_user["role"]})
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=raw_token,
        httponly=True,
        secure=SESSION_COOKIE_SECURE,
        samesite=SESSION_COOKIE_SAMESITE,
        max_age=SESSION_TTL_SECONDS,
    )
    return response


@app.post("/api/auth/register")
def register(payload: RegisterPayload):
    email = payload.email.strip().lower()
    if "@" not in email:
        raise HTTPException(status_code=422, detail="A valid email is required")
    if len(payload.password) < 8:
        raise HTTPException(status_code=422, detail="Password must be at least 8 characters")

    existing = storage.get_user_by_email(email)
    if existing is not None:
        raise HTTPException(status_code=409, detail="User already exists")

    user = storage.create_user(email=email, password_hash=hash_password(payload.password))
    return {"id": user["id"], "email": user["email"], "role": user["role"]}


@app.post("/api/auth/login")
def login(payload: LoginPayload):
    email = payload.email.strip().lower()
    user = storage.get_user_by_email(email)
    if user is None or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    raw_token = generate_session_token()
    storage.create_session(user_id=user["id"], token_hash=hash_session_token(raw_token), ttl_seconds=SESSION_TTL_SECONDS)

    response = JSONResponse(content={"id": user["id"], "email": user["email"], "role": user["role"]})
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=raw_token,
        httponly=True,
        secure=SESSION_COOKIE_SECURE,
        samesite=SESSION_COOKIE_SAMESITE,
        max_age=SESSION_TTL_SECONDS,
    )
    return response


@app.post("/api/auth/logout")
def logout(request: Request):
    session_token = request.cookies.get(SESSION_COOKIE_NAME)
    if session_token:
        try:
            storage.revoke_session(hash_session_token(session_token))
        except Exception:
            pass

    response = JSONResponse(content={"status": "logged_out"})
    response.delete_cookie(SESSION_COOKIE_NAME)
    return response


@app.get("/api/auth/me")
def me(request: Request):
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return {"sub": user["sub"], "role": user.get("role", "user")}


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
