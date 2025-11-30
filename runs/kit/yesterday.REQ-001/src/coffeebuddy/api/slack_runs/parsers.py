from __future__ import annotations

import shlex
from datetime import datetime, time, timezone
from typing import Iterable

from coffeebuddy.api.slack_runs.models import RunCommandOptions


def parse_command_text(text: str) -> RunCommandOptions:
    options = RunCommandOptions(errors=[])
    normalized = text.strip()
    if not normalized:
        return options

    tokens = shlex.split(normalized)
    for token in tokens:
        if "=" not in token:
            continue
        key, value = token.split("=", 1)
        key = key.lower()
        value = value.strip()

        if key in {"pickup", "pickup_time"}:
            _apply_pickup_time(value, options)
        elif key in {"note", "pickup_note"}:
            if len(value) > 120:
                options.errors.append("Pickup note must be <= 120 characters.")
            else:
                options.pickup_note = value
        else:
            options.errors.append(f"Unknown parameter '{key}'.")

    if not options.errors:
        options.errors = None
    return options


def _apply_pickup_time(value: str, options: RunCommandOptions) -> None:
    try:
        options.pickup_time = _parse_pickup_time(value)
    except ValueError:
        options.errors.append("pickup_time must be ISO-8601 date-time or HH:MM (24h).")


def _parse_pickup_time(value: str) -> datetime:
    if len(value) == 5 and value[2] == ":":
        hour, minute = map(int, value.split(":"))
        today = datetime.now(timezone.utc).date()
        return datetime.combine(today, time(hour=hour, minute=minute, tzinfo=timezone.utc))

    parsed = datetime.fromisoformat(value)
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)