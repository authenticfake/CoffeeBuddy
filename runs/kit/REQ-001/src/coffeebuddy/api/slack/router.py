from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Callable, Mapping
from urllib.parse import parse_qs

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import JSONResponse

from .commands import SlashCommandHandler, SlashCommandRequest
from .config import SlackConfig
from .errors import (
    SlackCommandValidationError,
    SlackInteractionValidationError,
    SlackVerificationError,
)
from .interactions import InteractionHandler
from .signature import SlackRequestVerifier

LOGGER = logging.getLogger("coffeebuddy.api.slack.router")


def create_slack_router(
    *,
    config: SlackConfig,
    clock: Callable[[], datetime] | None = None,
    logger: logging.Logger | None = None,
) -> APIRouter:
    """
    Build a FastAPI router exposing Slack slash command and interaction endpoints.

    Args:
        config: Slack configuration with signing secret and tolerances.
        clock: Optional clock override for deterministic testing.
        logger: Optional logger; defaults to module logger.

    Returns:
        APIRouter ready to be mounted under the main application.
    """
    router = APIRouter()
    log = logger or LOGGER
    verifier = SlackRequestVerifier(
        config.signing_secret,
        tolerance_seconds=config.request_tolerance_seconds,
        clock=clock or (lambda: datetime.now(timezone.utc)),
    )
    command_handler = SlashCommandHandler(clock=clock)
    interaction_handler = InteractionHandler()

    @router.post("/slack/command")
    async def slack_command(request: Request) -> JSONResponse:
        raw_body = await request.body()
        correlation_id = _derive_correlation_id(request.headers)

        try:
            verifier.verify(request.headers, raw_body)
        except SlackVerificationError as exc:
            log.warning(
                "Rejected Slack command due to verification failure",
                extra={"correlation_id": correlation_id},
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Slack signature.",
            ) from exc

        form = parse_qs(raw_body.decode("utf-8"))
        try:
            command = SlashCommandRequest.from_form(form)
            response_payload = command_handler.handle(command, correlation_id=correlation_id)
            log.info(
                "Slash command accepted",
                extra={
                    "correlation_id": correlation_id,
                    "channel_id": command.channel_id,
                    "user_id": command.user_id,
                },
            )
        except SlackCommandValidationError as exc:
            response_payload = command_handler.handle_invalid(
                correlation_id=correlation_id, error=str(exc)
            )
            log.info(
                "Slash command invalid",
                extra={"correlation_id": correlation_id, "error": str(exc)},
            )

        return JSONResponse(content=response_payload)

    @router.post("/slack/interaction")
    async def slack_interaction(request: Request) -> JSONResponse:
        raw_body = await request.body()
        correlation_id = _derive_correlation_id(request.headers)

        try:
            verifier.verify(request.headers, raw_body)
        except SlackVerificationError as exc:
            log.warning(
                "Rejected Slack interaction due to verification failure",
                extra={"correlation_id": correlation_id},
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Slack signature.",
            ) from exc

        form = parse_qs(raw_body.decode("utf-8"))
        payload_raw = next(iter(form.get("payload", [])), None)

        try:
            payload = interaction_handler.parse_payload(payload_raw)
        except SlackInteractionValidationError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
            ) from exc

        response_payload = interaction_handler.handle(payload, correlation_id=correlation_id)
        log.info(
            "Interaction acknowledged",
            extra={
                "correlation_id": correlation_id,
                "channel_id": (payload.get("channel") or {}).get("id"),
                "user_id": (payload.get("user") or {}).get("id"),
            },
        )
        return JSONResponse(content=response_payload)

    return router


def _derive_correlation_id(headers: Mapping[str, str]) -> str:
    for key in ("X-Correlation-ID", "X-Request-ID", "x-correlation-id", "x-request-id"):
        if headers.get(key):
            return headers[key]
    from uuid import uuid4

    return str(uuid4())