import asyncio
import hashlib
import hmac
import json
import os
import time
from datetime import datetime, timezone

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from coffeebuddy.app import create_app
from coffeebuddy.events.run import RunCreatedEvent, RunEventPublisher
from coffeebuddy.infra.db import Base
from coffeebuddy.models.run import Run
from coffeebuddy.config import Settings


class FakePublisher(RunEventPublisher):
    def __init__(self) -> None:
        self.events: list[RunCreatedEvent] = []

    def publish_run_created(self, event: RunCreatedEvent) -> None:
        self.events.append(event)


def _make_signature(secret: str, timestamp: str, body: bytes) -> str:
    sig_basestring = f"v0:{timestamp}:{body.decode()}".encode()
    digest = hmac.new(secret.encode(), sig_basestring, hashlib.sha256).hexdigest()
    return f"v0={digest}"


@pytest.fixture
def test_app(tmp_path):
    os.environ["COFFEEBUDDY_SLACK_SIGNING_SECRET"] = "test-signing-secret"
    settings = Settings(
        slack_signing_secret="test-signing-secret",
        database_url="sqlite+pysqlite:///:memory:",
        kafka_bootstrap_servers="localhost:9092",
    )

    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    publisher = FakePublisher()

    app = create_app(
        settings=settings,
        session_factory=session_factory,
        event_publisher=publisher,
    )
    app.state.publisher = publisher  # attach for assertions
    app.state.session_factory = session_factory
    return app


@pytest.mark.asyncio
async def test_slash_command_requires_valid_signature(test_app):
    client = AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test")
    body = b"token=abc"
    timestamp = str(int(time.time()))
    headers = {
        "X-Slack-Request-Timestamp": timestamp,
        "X-Slack-Signature": "invalid",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    response = await client.post("/slack/commands", content=body, headers=headers)
    assert response.status_code == 401
    await client.aclose()


@pytest.mark.asyncio
async def test_slash_command_creates_run_and_emits_event(test_app):
    client = AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test")
    body = (
        "token=abc&team_id=T1&channel_id=C1&channel_name=general&user_id=U1&user_name=alex"
        "&text=pickup=2030-01-01T09:00:00+00:00 note=Lobby&trigger_id=123&response_url=https://example"
    ).encode()
    timestamp = str(int(time.time()))
    signature = _make_signature("test-signing-secret", timestamp, body)
    headers = {
        "X-Slack-Request-Timestamp": timestamp,
        "X-Slack-Signature": signature,
        "Content-Type": "application/x-www-form-urlencoded",
    }

    response = await client.post("/slack/commands", content=body, headers=headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["response_type"] == "in_channel"
    assert any("Lobby" in block.get("text", "") for block in payload["blocks"] if block.get("type") == "section")

    session = test_app.state.session_factory()
    runs = session.query(Run).all()
    assert len(runs) == 1
    run = runs[0]
    assert run.channel_id == "C1"
    assert run.pickup_note == "Lobby"
    assert run.pickup_time == datetime(2030, 1, 1, 9, tzinfo=timezone.utc)

    publisher: FakePublisher = test_app.state.publisher
    assert len(publisher.events) == 1
    assert publisher.events[0].run_id == run.id
    await client.aclose()