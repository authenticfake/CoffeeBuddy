from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from starlette.responses import JSONResponse

from coffeebuddy.api.slack_runs.models import SlackCommandPayload
from coffeebuddy.api.slack_runs.parsers import parse_command_text
from coffeebuddy.api.slack_runs.service import SlackRunCommandService
from coffeebuddy.api.slack_runs.signature import SlackSignatureVerifier, SlackVerificationError
from coffeebuddy.api.slack_runs.dependencies import (
    get_run_event_publisher,
    get_session,
    get_settings,
)
from coffeebuddy.events.run import RunEventPublisher

router = APIRouter(tags=["slack"])


@router.post("/slack/commands")
async def handle_slack_command(
    request: Request,
    session=Depends(get_session),
    publisher: RunEventPublisher = Depends(get_run_event_publisher),
    settings=Depends(get_settings),
):
    body = await request.body()

    verifier = SlackSignatureVerifier(
        signing_secret=settings.slack_signing_secret,
        tolerance_seconds=settings.slack_timestamp_tolerance_seconds,
    )
    try:
        verifier.verify(
            timestamp=request.headers.get("X-Slack-Request-Timestamp"),
            signature=request.headers.get("X-Slack-Signature"),
            body=body,
        )
    except SlackVerificationError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    payload = _parse_form_payload(body)

    command = SlackCommandPayload(
        token=payload.get("token", ""),
        team_id=payload.get("team_id", ""),
        channel_id=payload.get("channel_id", ""),
        channel_name=payload.get("channel_name", ""),
        user_id=payload.get("user_id", ""),
        user_name=payload.get("user_name", ""),
        text=payload.get("text", ""),
        trigger_id=payload.get("trigger_id", ""),
        response_url=payload.get("response_url", ""),
    )

    options = parse_command_text(command.text)
    if options.has_errors():
        return JSONResponse(
            content={
                "response_type": "ephemeral",
                "text": "\n".join(options.errors or []),
            }
        )

    service = SlackRunCommandService(session=session, event_publisher=publisher)
    response = service.handle(command=command, options=options)

    return JSONResponse(content=response)


def _parse_form_payload(body: bytes) -> dict[str, str]:
    from urllib.parse import parse_qs

    parsed = parse_qs(body.decode())
    return {key: values[0] for key, values in parsed.items()}