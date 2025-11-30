import asyncio
from typing import Any

import pytest
from httpx import AsyncClient
from httpx import ASGITransport
from prometheus_client import CollectorRegistry, Counter

from coffeebuddy.infrastructure.runtime import Settings, create_app
from coffeebuddy.infrastructure.runtime.clients import OryClient, VaultClient


class _HealthyVaultClient(VaultClient):
    async def health_check(self) -> bool:  # type: ignore[override]
        return True


class _UnhealthyVaultClient(VaultClient):
    async def health_check(self) -> bool:  # type: ignore[override]
        return False


class _HealthyOryClient(OryClient):
    async def health_check(self) -> bool:  # type: ignore[override]
        return True


class _UnhealthyOryClient(OryClient):
    async def health_check(self) -> bool:  # type: ignore[override]
        return False


@pytest.mark.asyncio
async def test_health_live_ok() -> None:
    app = create_app(
        Settings(), vault_client_factory=lambda s: _HealthyVaultClient(), ory_client_factory=lambda s: _HealthyOryClient()
    )
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        resp = await client.get("/health/live")
    assert resp.status_code == 200
    assert resp.json()["status"] == "live"


@pytest.mark.asyncio
async def test_health_ready_ok_when_all_dependencies_healthy() -> None:
    app = create_app(
        Settings(), vault_client_factory=lambda s: _HealthyVaultClient(), ory_client_factory=lambda s: _HealthyOryClient()
    )

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        resp = await client.get("/health/ready")

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["status"] == "ready"
    assert payload["components"]["vault"] == "ok"
    assert payload["components"]["ory"] == "ok"


@pytest.mark.asyncio
async def test_health_ready_503_when_vault_unhealthy() -> None:
    app = create_app(
        Settings(),
        vault_client_factory=lambda s: _UnhealthyVaultClient(),
        ory_client_factory=lambda s: _HealthyOryClient(),
    )

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        resp = await client.get("/health/ready")

    assert resp.status_code == 503
    payload = resp.json()
    assert payload["detail"]["status"] == "degraded"
    assert payload["detail"]["components"]["vault"] == "unavailable"
    assert payload["detail"]["components"]["ory"] == "ok"


@pytest.mark.asyncio
async def test_health_ready_503_when_ory_unhealthy() -> None:
    app = create_app(
        Settings(),
        vault_client_factory=lambda s: _HealthyVaultClient(),
        ory_client_factory=lambda s: _UnhealthyOryClient(),
    )

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        resp = await client.get("/health/ready")

    assert resp.status_code == 503
    payload = resp.json()
    assert payload["detail"]["status"] == "degraded"
    assert payload["detail"]["components"]["vault"] == "ok"
    assert payload["detail"]["components"]["ory"] == "unavailable"


@pytest.mark.asyncio
async def test_metrics_endpoint_uses_registry_and_returns_prometheus_format() -> None:
    registry = CollectorRegistry()
    # Create a simple counter so that the output is non-empty and deterministic.
    c = Counter("coffeebuddy_test_counter_total", "Test counter", registry=registry)
    c.inc()

    app = create_app(
        Settings(), vault_client_factory=lambda s: _HealthyVaultClient(), ory_client_factory=lambda s: _HealthyOryClient(), registry=registry
    )

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        resp = await client.get("/metrics")

    assert resp.status_code == 200
    assert "coffeebuddy_test_counter_total" in resp.text