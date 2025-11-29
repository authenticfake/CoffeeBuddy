from __future__ import annotations

from datetime import datetime, timezone

from coffeebuddy.models.run import Run


class SlackMessageBuilder:
    """Constructs Slack block-kit payloads."""

    @staticmethod
    def build_run_created(run: Run) -> dict:
        blocks: list[dict] = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "☕ Coffee run started!", "emoji": True},
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Channel*\n<{run.channel_id}>"},
                    {"type": "mrkdwn", "text": f"*Initiator*\n<@{run.initiator_user_id}>"},
                ],
            },
            {
                "type": "context",
                "elements": [
                    {"type": "mrkdwn", "text": f"Run ID: `{run.id}`"},
                    {"type": "mrkdwn", "text": f"Correlation: `{run.correlation_id}`"},
                ],
            },
        ]

        if run.pickup_time:
            pickup_display = run.pickup_time.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
            blocks.append(
                {
                    "type": "section",
                    "fields": [{"type": "mrkdwn", "text": f"*Pickup time*\n{pickup_display}"}],
                }
            )

        if run.pickup_note:
            blocks.append(
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"*Pickup note*\n{run.pickup_note}"},
                }
            )

        blocks.append(
            {
                "type": "actions",
                "elements": [
                    {"type": "button", "text": {"type": "plain_text", "text": "Place order"}, "action_id": "order:new"},
                    {"type": "button", "text": {"type": "plain_text", "text": "Use last order"}, "action_id": "order:reuse"},
                    {"type": "button", "text": {"type": "plain_text", "text": "Close run"}, "style": "danger", "action_id": "run:close"},
                ],
            }
        )

        return {
            "response_type": "in_channel",
            "text": "Coffee run is live.",
            "blocks": blocks,
        }