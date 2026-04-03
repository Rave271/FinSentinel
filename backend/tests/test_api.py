import asyncio

import httpx

from app.main import app, live_signal_stream, rate_limiter
from app.security import create_access_token


async def _request(method: str, url: str, **kwargs):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        return await client.request(method, url, **kwargs)


def test_health_endpoint_reports_backend_state():
    response = asyncio.run(_request("GET", "/api/health"))

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["cors"] is True
    assert "database" in payload


def test_signal_endpoint_returns_model_payload():
    response = asyncio.run(_request("GET", "/api/signal/INFY"))

    assert response.status_code == 200
    payload = response.json()
    assert payload["ticker"] == "INFY"
    assert payload["signal"]["label"] in {"BUY", "HOLD", "SELL"}
    assert len(payload["top_factors"]) == 3


def test_news_endpoint_filters_by_ticker():
    response = asyncio.run(_request("GET", "/api/news/INFY"))

    assert response.status_code == 200
    payload = response.json()
    assert payload["ticker"] == "INFY"
    assert isinstance(payload["items"], list)


def test_divergence_endpoint_returns_severity():
    response = asyncio.run(_request("GET", "/api/divergence/INFY"))

    assert response.status_code == 200
    payload = response.json()
    assert payload["ticker"] == "INFY"
    assert payload["severity"] in {"low", "medium", "high"}
    assert "divergence_score" in payload


def test_portfolio_endpoint_requires_authentication():
    response = asyncio.run(
        _request("POST", "/api/portfolio/analyze", json={"holdings": [{"ticker": "INFY", "quantity": 10}]})
    )

    assert response.status_code == 401


def test_portfolio_endpoint_returns_analysis_for_authenticated_user():
    token = create_access_token("raghav")
    response = asyncio.run(
        _request(
            "POST",
            "/api/portfolio/analyze",
            headers={"Authorization": f"Bearer {token}"},
            json={"holdings": [{"ticker": "INFY", "quantity": 10, "average_cost": 1200}]},
        )
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["user"] == "raghav"
    assert payload["portfolio_size"] == 1
    assert payload["holdings"][0]["ticker"] == "INFY"


def test_websocket_endpoint_pushes_snapshot():
    class FakeWebSocket:
        def __init__(self):
            self.messages = []

        async def accept(self):
            return None

        async def send_json(self, payload):
            self.messages.append(payload)
            raise RuntimeError("stop-after-first-push")

    websocket = FakeWebSocket()
    try:
        asyncio.run(live_signal_stream(websocket, "INFY"))
    except RuntimeError as exc:
        assert str(exc) == "stop-after-first-push"

    payload = websocket.messages[0]

    assert payload["ticker"] == "INFY"
    assert payload["type"] == "live_signal_snapshot"


def test_rate_limit_blocks_repeated_requests():
    rate_limiter.reset()
    original_max = rate_limiter.max_requests
    original_window = rate_limiter.window_seconds
    rate_limiter.max_requests = 1
    rate_limiter.window_seconds = 60

    try:
        first = asyncio.run(_request("GET", "/api/signal/INFY"))
        second = asyncio.run(_request("GET", "/api/signal/INFY"))
    finally:
        rate_limiter.max_requests = original_max
        rate_limiter.window_seconds = original_window
        rate_limiter.reset()

    assert first.status_code == 200
    assert second.status_code == 429
