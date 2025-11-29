from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Tuple


@dataclass(frozen=True, slots=True)
class AdminActor:
    """Represents the Slack user invoking an admin action."""

    user_id: str
    slack_user_id: str
    slack_roles: Tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ChannelConfigPatch:
    """Partial configuration updates supported by the admin command."""

    reminder_offset_minutes: int | None = None
    fairness_window_runs: int | None = None
    data_retention_days: int | None = None
    reminders_enabled: bool | None = None
    last_call_enabled: bool | None = None
    last_call_lead_minutes: int | None = None


class ChannelAdminActionType(str, Enum):
    """Valid audit action types accepted by persistence."""

    ENABLE = "enable"
    DISABLE = "disable"
    UPDATE_CONFIG = "update_config"
    DATA_RESET = "data_reset"


@dataclass(frozen=True, slots=True)
class ChannelConfigUpdateResult:
    """Outcome returned to the Slack layer after config updates."""

    channel_id: str
    applied_fields: Tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ChannelStateChangeResult:
    """Represents the state toggle (enable/disable) effect."""

    channel_id: str
    enabled: bool
    action_type: ChannelAdminActionType


@dataclass(frozen=True, slots=True)
class DataResetResult:
    """Summary of the counts removed during a channel data reset."""

    channel_id: str
    orders_deleted: int
    runs_deleted: int
    preferences_deleted: int
    runner_stats_deleted: int