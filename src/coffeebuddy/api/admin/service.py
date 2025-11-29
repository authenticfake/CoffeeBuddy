from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable, Dict

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from coffeebuddy.api.admin.authorizer import SlackAdminAuthorizer
from coffeebuddy.api.admin.exceptions import (
    ChannelConfigValidationError,
    ChannelNotFoundError,
)
from coffeebuddy.api.admin.models import (
    AdminActor,
    ChannelAdminActionType,
    ChannelConfigPatch,
    ChannelConfigUpdateResult,
    ChannelStateChangeResult,
    DataResetResult,
)
from coffeebuddy.core.audit import AdminAuditLogger
from coffeebuddy.infra.db.models import Channel, Order, Run, RunnerStat, UserPreference

Clock = Callable[[], datetime]


class AdminService:
    """Coordinates validation, authorization, and auditing for admin operations."""

    def __init__(
        self,
        session: Session,
        *,
        authorizer: SlackAdminAuthorizer,
        audit_logger: AdminAuditLogger | None = None,
        clock: Clock | None = None,
    ) -> None:
        self._session = session
        self._authorizer = authorizer
        self._audit = audit_logger or AdminAuditLogger(session)
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def update_channel_config(
        self,
        *,
        slack_channel_id: str,
        actor: AdminActor,
        patch: ChannelConfigPatch,
    ) -> ChannelConfigUpdateResult:
        channel = self._get_channel(slack_channel_id)
        self._authorizer.assert_authorized(actor)
        updates = self._build_config_updates(channel, patch)
        if not updates:
            return ChannelConfigUpdateResult(
                channel_id=str(channel.id),
                applied_fields=(),
            )
        timestamp = self._clock()
        for field, value in updates.items():
            setattr(channel, field, value)
        channel.updated_at = timestamp
        self._audit.log_action(
            channel_id=channel.id,
            admin_user_id=actor.user_id,
            action_type=ChannelAdminActionType.UPDATE_CONFIG.value,
            details={"updated_fields": updates},
        )
        self._session.flush()
        return ChannelConfigUpdateResult(
            channel_id=str(channel.id),
            applied_fields=tuple(updates.keys()),
        )

    def set_channel_enabled(
        self,
        *,
        slack_channel_id: str,
        actor: AdminActor,
        enabled: bool,
        reason: str | None = None,
    ) -> ChannelStateChangeResult:
        channel = self._get_channel(slack_channel_id)
        self._authorizer.assert_authorized(actor)
        timestamp = self._clock()
        previous_state = bool(channel.enabled)
        channel.enabled = enabled
        channel.updated_at = timestamp
        action_type = (
            ChannelAdminActionType.ENABLE if enabled else ChannelAdminActionType.DISABLE
        )
        self._audit.log_action(
            channel_id=channel.id,
            admin_user_id=actor.user_id,
            action_type=action_type.value,
            details={
                "reason": reason or "unspecified",
                "previous_state": previous_state,
                "changed": previous_state != enabled,
            },
        )
        self._session.flush()
        return ChannelStateChangeResult(
            channel_id=str(channel.id),
            enabled=enabled,
            action_type=action_type,
        )

    def reset_channel_data(
        self,
        *,
        slack_channel_id: str,
        actor: AdminActor,
    ) -> DataResetResult:
        channel = self._get_channel(slack_channel_id)
        self._authorizer.assert_authorized(actor)
        counts = self._purge_channel_data(channel_id=channel.id)
        timestamp = self._clock()
        channel.last_reset_at = timestamp
        channel.updated_at = timestamp
        self._audit.log_action(
            channel_id=channel.id,
            admin_user_id=actor.user_id,
            action_type=ChannelAdminActionType.DATA_RESET.value,
            details=counts,
        )
        self._session.flush()
        return DataResetResult(
            channel_id=str(channel.id),
            **counts,
        )

    def _get_channel(self, slack_channel_id: str) -> Channel:
        stmt = select(Channel).where(Channel.slack_channel_id == slack_channel_id)
        channel = self._session.execute(stmt).scalar_one_or_none()
        if not channel:
            raise ChannelNotFoundError(slack_channel_id)
        return channel

    def _build_config_updates(
        self,
        channel: Channel,
        patch: ChannelConfigPatch,
    ) -> Dict[str, object]:
        updates: Dict[str, object] = {}
        if patch.reminder_offset_minutes is not None:
            self._ensure_range(
                "reminder_offset_minutes", patch.reminder_offset_minutes, 1, 60
            )
            updates["reminder_offset_minutes"] = patch.reminder_offset_minutes
        if patch.fairness_window_runs is not None:
            self._ensure_range(
                "fairness_window_runs", patch.fairness_window_runs, 1, 50
            )
            updates["fairness_window_runs"] = patch.fairness_window_runs
        if patch.data_retention_days is not None:
            self._ensure_range(
                "data_retention_days", patch.data_retention_days, 30, 365
            )
            updates["data_retention_days"] = patch.data_retention_days
        if patch.reminders_enabled is not None:
            updates["reminders_enabled"] = patch.reminders_enabled
        if patch.last_call_enabled is not None:
            updates["last_call_enabled"] = patch.last_call_enabled
        if patch.last_call_lead_minutes is not None:
            self._ensure_range(
                "last_call_lead_minutes", patch.last_call_lead_minutes, 1, 30
            )
            updates["last_call_lead_minutes"] = patch.last_call_lead_minutes
        if (
            patch.last_call_enabled is True
            and patch.last_call_lead_minutes is None
            and channel.last_call_lead_minutes is None
        ):
            raise ChannelConfigValidationError(
                "last_call_lead_minutes",
                "Lead time must be provided when enabling last call reminders.",
            )
        return updates

    def _ensure_range(self, field: str, value: int, minimum: int, maximum: int) -> None:
        if not minimum <= value <= maximum:
            raise ChannelConfigValidationError(
                field,
                f"Value {value} must be between {minimum} and {maximum}.",
            )

    def _purge_channel_data(self, *, channel_id: str) -> Dict[str, int]:
        run_ids_subquery = select(Run.id).where(Run.channel_id == channel_id)
        orders_deleted = self._execute_delete(
            delete(Order).where(Order.run_id.in_(run_ids_subquery))
        )
        runs_deleted = self._execute_delete(
            delete(Run).where(Run.channel_id == channel_id)
        )
        preferences_deleted = self._execute_delete(
            delete(UserPreference).where(UserPreference.channel_id == channel_id)
        )
        runner_stats_deleted = self._execute_delete(
            delete(RunnerStat).where(RunnerStat.channel_id == channel_id)
        )
        return {
            "orders_deleted": orders_deleted,
            "runs_deleted": runs_deleted,
            "preferences_deleted": preferences_deleted,
            "runner_stats_deleted": runner_stats_deleted,
        }

    def _execute_delete(self, statement) -> int:
        result = self._session.execute(statement)
        return max(0, result.rowcount or 0)