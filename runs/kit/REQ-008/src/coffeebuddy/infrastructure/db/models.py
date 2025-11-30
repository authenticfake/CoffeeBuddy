from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class RunStatus(StrEnum):
    OPEN = "open"
    CLOSED = "closed"
    CANCELED = "canceled"
    FAILED = "failed"


class Base(DeclarativeBase):
    """Declarative SQLAlchemy base."""


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class SerializableMixin:
    """
    Helper to convert ORM instances into primitive dictionaries for logging/testing purposes.
    """

    def as_dict(self) -> dict[str, Any]:
        return {column.key: getattr(self, column.key) for column in self.__table__.columns}  # type: ignore[attr-defined]


class User(Base, SerializableMixin, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default="uuid_generate_v4()"
    )
    slack_user_id: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Channel(Base, SerializableMixin, TimestampMixin):
    __tablename__ = "channels"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default="uuid_generate_v4()"
    )
    slack_channel_id: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    reminder_offset_minutes: Mapped[int] = mapped_column(
        Integer, nullable=False, default=5
    )
    fairness_window_runs: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    data_retention_days: Mapped[int] = mapped_column(Integer, nullable=False, default=90)
    reminders_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_call_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_call_lead_minutes: Mapped[int | None] = mapped_column(Integer)
    last_reset_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        CheckConstraint(
            "reminder_offset_minutes BETWEEN 1 AND 60", name="chk_channels_reminder_offset"
        ),
        CheckConstraint(
            "fairness_window_runs BETWEEN 1 AND 50", name="chk_channels_fairness_window"
        ),
        CheckConstraint(
            "data_retention_days BETWEEN 30 AND 365", name="chk_channels_retention"
        ),
    )


class Run(Base, SerializableMixin, TimestampMixin):
    __tablename__ = "runs"
    __table_args__ = (
        CheckConstraint(
            "status IN ('open','closed','canceled','failed')",
            name="chk_runs_status",
        ),
        Index("idx_runs_channel_status", "channel_id", "status"),
        Index("idx_runs_runner", "runner_user_id", "started_at"),
    )

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default="uuid_generate_v4()"
    )
    channel_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("channels.id", ondelete="RESTRICT"), nullable=False
    )
    initiator_user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    runner_user_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    status: Mapped[str] = mapped_column(String(16), default=RunStatus.OPEN.value, nullable=False)
    pickup_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    pickup_note: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failure_reason: Mapped[str | None] = mapped_column(Text)


class Order(Base, SerializableMixin, TimestampMixin):
    __tablename__ = "orders"
    __table_args__ = (
        UniqueConstraint("run_id", "user_id", name="uq_orders_run_user"),
        Index("idx_orders_run", "run_id"),
        Index("idx_orders_user", "user_id"),
    )

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default="uuid_generate_v4()"
    )
    run_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("runs.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    order_text: Mapped[str] = mapped_column(Text, nullable=False)
    is_final: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    canceled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class UserPreference(Base, SerializableMixin, TimestampMixin):
    __tablename__ = "user_preferences"
    __table_args__ = (
        UniqueConstraint("user_id", "channel_id", name="uq_preferences_user_channel"),
    )

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default="uuid_generate_v4()"
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
        UUID(as_uuid=True), primary_key=True, server_default="uuid_generate_v4()"
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    channel_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("channels.id", ondelete="CASCADE"), nullable=False
    )
    runs_served_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ChannelAdminAction(Base, SerializableMixin):
    __tablename__ = "channel_admin_actions"
    __table_args__ = (
        Index("idx_channel_admin_actions_channel", "channel_id"),
        CheckConstraint(
            "action_type IN ('enable','disable','update_config','data_reset')",
            name="chk_channel_admin_actions_type",
        ),
    )

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default="uuid_generate_v4()"
    )
    channel_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("channels.id", ondelete="CASCADE"), nullable=False
    )
    admin_user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    action_type: Mapped[str] = mapped_column(String(32), nullable=False)
    action_details: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )