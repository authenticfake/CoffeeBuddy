from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Mapping

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Declarative base for CoffeeBuddy ORM models."""


class SerializableMixin:
    """Provides deterministic serialization for domain models."""

    def to_dict(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {}
        for key in self.__mapper__.columns.keys():  # type: ignore[attr-defined]
            value = getattr(self, key)
            if isinstance(value, datetime):
                payload[key] = value.isoformat()
            else:
                payload[key] = value
        return payload


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )


class RunStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"
    CANCELED = "canceled"
    FAILED = "failed"


class User(Base, SerializableMixin, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default="uuid_generate_v4()",
    )
    slack_user_id: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class Channel(Base, SerializableMixin, TimestampMixin):
    __tablename__ = "channels"
    __table_args__ = (
        CheckConstraint("reminder_offset_minutes BETWEEN 1 AND 60", name="chk_channel_reminder_offset"),
        CheckConstraint("fairness_window_runs BETWEEN 1 AND 50", name="chk_channel_fairness_window"),
        CheckConstraint("data_retention_days BETWEEN 30 AND 365", name="chk_channel_retention"),
    )

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default="uuid_generate_v4()",
    )
    slack_channel_id: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    reminder_offset_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    fairness_window_runs: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    data_retention_days: Mapped[int] = mapped_column(Integer, nullable=False, default=90)
    reminders_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_call_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_call_lead_minutes: Mapped[int | None] = mapped_column(Integer)
    last_reset_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Run(Base, SerializableMixin, TimestampMixin):
    __tablename__ = "runs"
    __table_args__ = (
        CheckConstraint(
            "status IN ('open','closed','canceled','failed')",
            name="chk_run_status",
        ),
        Index("idx_runs_channel_status", "channel_id", "status"),
        Index("idx_runs_runner", "runner_user_id", "started_at"),
    )

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default="uuid_generate_v4()",
    )
    channel_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("channels.id", ondelete="RESTRICT"), nullable=False
    )
    initiator_user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    runner_user_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT")
    )
    status: Mapped[RunStatus] = mapped_column(String(16), nullable=False, default=RunStatus.OPEN.value)
    pickup_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    pickup_note: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failure_reason: Mapped[str | None] = mapped_column(Text)
    correlation_id: Mapped[str] = mapped_column(String(64), nullable=False)


class Order(Base, SerializableMixin, TimestampMixin):
    __tablename__ = "orders"
    __table_args__ = (
        UniqueConstraint("run_id", "user_id", name="uq_orders_run_user"),
        Index("idx_orders_run", "run_id"),
        Index("idx_orders_user", "user_id"),
    )

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default="uuid_generate_v4()",
    )
    run_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("runs.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    order_text: Mapped[str] = mapped_column(Text, nullable=False)
    is_final: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    provenance: Mapped[str] = mapped_column(String(32), nullable=False, default="manual")
    canceled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class UserPreference(Base, SerializableMixin, TimestampMixin):
    __tablename__ = "user_preferences"
    __table_args__ = (UniqueConstraint("user_id", "channel_id", name="uq_preferences_user_channel"),)

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default="uuid_generate_v4()",
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    channel_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("channels.id", ondelete="CASCADE"), nullable=False
    )
    last_order_text: Mapped[str] = mapped_column(Text, nullable=False)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class RunnerStat(Base, SerializableMixin, TimestampMixin):
    __tablename__ = "runner_stats"
    __table_args__ = (
        UniqueConstraint("user_id", "channel_id", name="uq_runner_stats_user_channel"),
        Index("idx_runner_stats_usage", "channel_id", "runs_served_count", "last_run_at"),
    )

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default="uuid_generate_v4()",
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    channel_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("channels.id", ondelete="CASCADE"), nullable=False
    )
    runs_served_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ChannelAdminAction(Base, SerializableMixin):
    __tablename__ = "channel_admin_actions"
    __table_args__ = (
        CheckConstraint(
            "action_type IN ('enable','disable','update_config','data_reset')",
            name="chk_admin_action_type",
        ),
        Index("idx_channel_admin_actions_channel", "channel_id", "created_at"),
    )

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default="uuid_generate_v4()",
    )
    channel_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("channels.id", ondelete="CASCADE"), nullable=False
    )
    admin_user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    action_type: Mapped[str] = mapped_column(String(32), nullable=False)
    action_details: Mapped[Mapping[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)