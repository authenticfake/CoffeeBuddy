import json
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from coffeebuddy.infrastructure.runtime.app import create_app
from coffeebuddy.infrastructure.runtime.config import load_service_config
from coffeebuddy.infrastructure.runtime.probes import Probe, ProbeResult, ReadinessRegistry


class StaticProbe:
    def __init__(self, name: str, passed: bool = True):
        self.name = name
        self._passed = passed

    async def check(self) -> ProbeResult:
        return ProbeResult(name=self.name, passed=self._passed, detail="static", duration_ms=0.1)


@pytest.mark.anyio
async def test_health_endpoints_report_ready(monkeypatch, tmp_path):
    vault_token = tmp_path / "vault.token"
    vault_token.write_text("token")
    env = {
        "SLACK_SIGNING_SECRET": "secret",
        "SLACK_BOT_TOKEN": "token",
        "DATABASE_URL": "postgresql://user:pass@db:5432/coffeebuddy",
        "KAFKA_BROKERS": "kafka:9092",
        "VAULT_ADDR": "https://vault.local",
        "VAULT_ROLE": "coffeebuddy",
        "VAULT_TOKEN_PATH": str(vault_token),
        "ORY_ISSUER_URL": "https://ory.local",
        "ORY_AUDIENCE": "coffeebuddy",
        "ORY_CLIENT_ID": "coffeebuddy-client",
        "SERVICE_NAME": "cb",
    }
    for key, value in env.items():
        monkeypatch.setenv(key, value)

    config = load_service_config()
    readiness = ReadinessRegistry()
    readiness.register(StaticProbe("env"))
    app = create_app(config=config, readiness_registry=readiness)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        live = await client.get("/health/live")
        assert live.status_code == 200
        ready = await client.get("/health/ready")
        assert ready.status_code == 200
        data = ready.json()
        assert data["status"] == "ready"

        metrics = await client.get("/metrics")
        assert metrics.status_code == 200
        assert b"coffeebuddy_service_info" in metrics.content


@pytest.mark.anyio
async def test_readiness_fails_when_probe_fails(monkeypatch, tmp_path):
    vault_token = tmp_path / "vault.token"
    vault_token.write_text("token")
    base_env = {
        "SLACK_SIGNING_SECRET": "secret",
        "SLACK_BOT_TOKEN": "token",
        "DATABASE_URL": "postgresql://user:pass@db:5432/coffeebuddy",
        "KAFKA_BROKERS": "kafka:9092",
        "VAULT_ADDR": "https://vault.local",
        "VAULT_ROLE": "coffeebuddy",
        "VAULT_TOKEN_PATH": str(vault_token),
        "ORY_ISSUER_URL": "https://ory.local",
        "ORY_AUDIENCE": "coffeebuddy",
        "ORY_CLIENT_ID": "coffeebuddy-client",
    }
    for key, value in base_env.items():
        monkeypatch.setenv(key, value)

    config = load_service_config()
    readiness = ReadinessRegistry()
    readiness.register(StaticProbe("db", passed=False))
    app = create_app(config=config, readiness_registry=readiness)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        ready = await client.get("/health/ready")
        assert ready.status_code == 503
        assert ready.json()["status"] == "not_ready"