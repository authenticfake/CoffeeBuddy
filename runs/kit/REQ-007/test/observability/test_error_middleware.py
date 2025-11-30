import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from coffeebuddy.observability.errors import CoffeeBuddyError
from coffeebuddy.observability.middleware import CorrelationIdMiddleware, ErrorHandlingMiddleware
from coffeebuddy.observability.metrics import build_metrics_suite


@pytest.mark.asyncio
async def test_error_handling_middleware_translates_domain_errors_and_records_metrics() -> None:
    suite = build_metrics_suite()
    app = FastAPI()
    app.add_middleware(CorrelationIdMiddleware)
    app.add_middleware(ErrorHandlingMiddleware, metrics=suite.request)

    @app.get("/boom")
    def boom() -> None:
        raise CoffeeBuddyError("Invalid input", status_code=400, error_code="invalid_command")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        resp = await client.get("/boom", headers={"X-Slack-Request-Type": "slash"})

    assert resp.status_code == 400
    assert resp.headers["X-Correlation-ID"]
    body = resp.json()
    assert body == {"ok": False, "error": "Invalid input", "code": "invalid_command"}

    metric_value = suite.registry.get_sample_value(
        "coffeebuddy_requests_total", labels={"type": "slash", "result": "client_error"}
    )
    assert metric_value == 1.0