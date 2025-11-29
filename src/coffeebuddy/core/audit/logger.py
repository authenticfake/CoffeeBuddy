from __future__ import annotations

from typing import Any, Mapping

from sqlalchemy.orm import Session

from coffeebuddy.infra.db.models import ChannelAdminAction


class AdminAuditLogger:
    """Persists channel admin actions for auditability."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def log_action(
        self,
        *,
        channel_id: str,
        admin_user_id: str,
        action_type: str,
        details: Mapping[str, Any] | None = None,
    ) -> ChannelAdminAction:
        entry = ChannelAdminAction(
            channel_id=channel_id,
            admin_user_id=admin_user_id,
            action_type=action_type,
            action_details=dict(details or {}),
        )
        self._session.add(entry)
        self._session.flush()
        return entry