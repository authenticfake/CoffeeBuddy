from __future__ import annotations

import hmac
import json
from datetime import datetime, timezone
from hashlib import sha256
from urllib.parse import urlencode

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from coffeebuddy.api.slack import SlackConfig, create_slack_router

FIXED_TIME = datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)


def _sign_payload(body: str, timestamp: str, secret: str) -> str:
    base = f"v0:{timestamp}:{body}"
    digest = hmac.new(secret.encode("utf-8"), base.encode("utf-8"), sha256).hexdigest()
    return f"v0={digest}"


def _build_app() -> FastAPI:
    config = SlackConfig(signing_secret="topsecret", request_tolerance_seconds=300)
    router = create_slack_router(config=config, clock=lambda: FIXED_TIME)
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.mark.asyncio
async def test_slash_command_success_returns_blocks() -> None:
    app = _build_app()
    body_dict = {
        "token": "test",
        "team_id": "T123",
        "team_domain": "coffee",
        "channel_id": "C123",
        "channel_name": "coffee-run",
        "user_id": "U123",
        "user_name": "barista",
        "command": "/coffee",
        "text": 'pickup=10:30 note="Lobby cafe"',
        "trigger_id": "111.222",
        "response_url": "https://example.com",
    }
    body = urlencode(body_dict)
    timestamp = str(int(FIXED_TIME.timestamp()))
    signature = _sign_payload(body, timestamp, "topsecret")

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        response = await client.post(
            "/slack/command",
            content=body,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "X-Slack-Request-Timestamp": timestamp,
                "X-Slack-Signature": signature,
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["response_type"] == "in_channel"
    assert any(block["type"] == "actions" for block in payload["blocks"])
    tracking_blocks = [b for b in payload["blocks"] if b["type"] == "context"]
    assert any("Tracking ID" in elem["text"] for block in tracking_blocks for elem in block["elements"])


@pytest.mark.asyncio
async def test_slash_command_invalid_signature_rejected() -> None:
    app = _build_app()
    body = "token=test"
    timestamp = str(int(FIXED_TIME.timestamp()))

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        response = await client.post(
            "/slack/command",
            content=body,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "X-Slack-Request-Timestamp": timestamp,
                "X-Slack-Signature": "v0=invalid",
            },
        )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_slash_command_invalid_text_returns_usage() -> None:
    app = _build_app()
    body_dict = {
        "token": "test",
        "team_id": "T123",
        "team_domain": "coffee",
        "channel_id": "C123",
        "channel_name": "coffee-run",
        "user_id": "U123",
        "user_name": "barista",
        "command": "/coffee",
        "text": "unknown=param",
        "trigger_id": "111.222",
        "response_url": "https://example.com",
    }
    body = urlencode(body_dict)
    timestamp = str(int(FIXED_TIME.timestamp()))
    signature = _sign_payload(body, timestamp, "topsecret")

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        response = await client.post(
            "/slack/command",
            content=body,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "X-Slack-Request-Timestamp": timestamp,
                "X-Slack-Signature": signature,
            },
        )

    payload = response.json()
    assert response.status_code == 200
    assert payload["response_type"] == "ephemeral"
    assert "Usage:" in payload["text"]


@pytest.mark.asyncio
async def test_interaction_acknowledged_when_signature_valid() -> None:
    app = _build_app()
    payload = {
        "type": "block_actions",
        "user": {"id": "U123"},
        "channel": {"id": "C123"},
        "actions": [{"action_id": "order:new"}],
    }
    body = urlencode({"payload": json.dumps(payload)})
    timestamp = str(int(FIXED_TIME.timestamp()))
    signature = _sign_payload(body, timestamp, "topsecret")

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        response = await client.post(
            "/slack/interaction",
            content=body,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "X-Slack-Request-Timestamp": timestamp,
                "X-Slack-Signature": signature,
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert data["response_type"] == "ephemeral"
    assert any("Tracking ID" in elem["text"] for elem in data["blocks"][-1]["elements"])