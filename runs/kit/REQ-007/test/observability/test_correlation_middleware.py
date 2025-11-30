import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from coffeebuddy.observability.correlation import get_request_context
from coffeebuddy.observability.middleware import CorrelationIdMiddleware


@pytest.mark.asyncio
async def test_correlation_id_middleware_respects_existing_header() -> None:
    app = FastAPI()
    app.add_middleware(CorrelationIdMiddleware)

    @app.get("/ping")
    def ping() -> dict:
        ctx = get_request_context()
        return {"correlation_id": ctx.correlation_id if ctx else None}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        resp = await client.get("/ping", headers={"X-Correlation-ID": "corr-123"})

    assert resp.status_code == 200
    assert resp.headers["X-Correlation-ID"] == "corr-123"
    assert resp.json()["correlation_id"] == "corr-123"


@pytest.mark.asyncio
async def test_correlation_id_middleware_generates_when_missing() -> None:
    app = FastAPI()
    app.add_middleware(CorrelationIdMiddleware)

    @app.get("/ping")
    def ping() -> dict:
        ctx = get_request_context()
        return {"correlation_id": ctx.correlation_id if ctx else None}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        resp = await client.get("/ping")

    assert resp.status_code == 200
    generated = resp.headers["X-Correlation-ID"]
    assert generated
    assert len(resp.json()["correlation_id"]) == len(generated)