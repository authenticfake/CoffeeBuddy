from __future__ import annotations

from typing import Any, Mapping

from .errors import SlackInteractionValidationError
from .commands import _tracking_block  # reuse context block


class InteractionHandler:
    """Acknowledges Slack block actions and surfaces tracking metadata."""

    def handle(self, payload: Mapping[str, Any], *, correlation_id: str) -> dict:
        channel = (payload.get("channel") or {}).get("id", "unknown-channel")
        user = (payload.get("user") or {}).get("id", "unknown-user")
        action_summary = self._describe_action(payload)

        text = (
            f"Action `{action_summary}` received for channel <#{channel}>. "
            "Hang tight while CoffeeBuddy processes the request."
        )

        return {
            "response_type": "ephemeral",
            "text": text,
            "blocks": [
                {"type": "section", "text": {"type": "mrkdwn", "text": f":white_check_mark: {text}"}},
                _tracking_block(correlation_id),
            ],
        }

    def parse_payload(self, payload_raw: str | None) -> Mapping[str, Any]:
        if not payload_raw:
            raise SlackInteractionValidationError("Missing interaction payload.")
        try:
            import json

            return json.loads(payload_raw)
        except ValueError as exc:
            raise SlackInteractionValidationError("Invalid JSON payload.") from exc

    def _describe_action(self, payload: Mapping[str, Any]) -> str:
        action = next(iter(payload.get("actions", [])), {})
        return action.get("action_id") or action.get("type") or "unknown"