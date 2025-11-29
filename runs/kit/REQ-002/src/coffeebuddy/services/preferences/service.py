from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from coffeebuddy.core.orders.models import Clock
from coffeebuddy.infra.db.models import UserPreference


class PreferenceService:
    """Manages per-channel user preference snapshots."""

    def __init__(self, session: Session, *, clock: Clock | None = None) -> None:
        self._session = session
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def get_preference(
        self, *, user_id: str | UUID, channel_id: str | UUID
    ) -> UserPreference | None:
        stmt = select(UserPreference).where(
            UserPreference.user_id == self._as_uuid(user_id),
            UserPreference.channel_id == self._as_uuid(channel_id),
        )
        return self._session.scalar(stmt)

    def set_preference(
        self, *, user_id: str | UUID, channel_id: str | UUID, order_text: str
    ) -> UserPreference:
        existing = self.get_preference(user_id=user_id, channel_id=channel_id)
        now = self._clock()
        if existing:
            existing.last_order_text = order_text
            existing.last_used_at = now
            existing.updated_at = now
            preference = existing
        else:
            preference = UserPreference(
                id=uuid4(),
                user_id=self._as_uuid(user_id),
                channel_id=self._as_uuid(channel_id),
                last_order_text=order_text,
                last_used_at=now,
                created_at=now,
                updated_at=now,
            )
            self._session.add(preference)
        return preference

    def mark_used(self, preference: UserPreference) -> UserPreference:
        preference.last_used_at = self._clock()
        preference.updated_at = preference.last_used_at
        return preference

    @staticmethod
    def _as_uuid(value: str | UUID) -> UUID:
        if isinstance(value, UUID):
            return value
        return UUID(value)