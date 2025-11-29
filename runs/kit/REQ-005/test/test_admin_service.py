from __future__ import annotations

import pathlib
import sys
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

ROOT_DIR = pathlib.Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from coffeebuddy.api.admin.authorizer import SlackAdminAuthorizer
from coffeebuddy.api.admin.exceptions import (
    AdminAuthorizationError,
    ChannelConfigValidationError,
)
from coffeebuddy.api.admin.models import AdminActor, ChannelConfigPatch
from coffeebuddy.api.admin.service import AdminService
from coffeebuddy.infra.db.models import (
    Base,
    Channel,
    ChannelAdminAction,
    Order,
    Run,
    RunStatus,
    RunnerStat,
    User,
    UserPreference,
)


@pytest.fixture()
def session():
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, future=True)
    with SessionLocal() as session:
        yield session


def test_update_channel_config_persists_values_and_audits(session):
    user = _create_user(session)
    channel = _create_channel(session)
    actor = AdminActor(
        user_id=str(user.id),
        slack_user_id=user.slack_user_id,
        slack_roles=("admin",),
    )
    service = AdminService(
        session,
        authorizer=SlackAdminAuthorizer(allowed_user_ids=[user.slack_user_id]),
    )
    patch = ChannelConfigPatch(
        reminder_offset_minutes=7,
        fairness_window_runs=4,
        data_retention_days=120,
        reminders_enabled=False,
        last_call_enabled=False,
    )

    result = service.update_channel_config(
        slack_channel_id=channel.slack_channel_id,
        actor=actor,
        patch=patch,
    )

    assert result.applied_fields == (
        "reminder_offset_minutes",
        "fairness_window_runs",
        "data_retention_days",
        "reminders_enabled",
        "last_call_enabled",
    )
    refreshed = session.get(Channel, channel.id)
    assert refreshed.reminder_offset_minutes == 7
    assert refreshed.data_retention_days == 120

    actions = (
        session.execute(
            select(ChannelAdminAction).where(
                ChannelAdminAction.channel_id == channel.id
            )
        )
        .scalars()
        .all()
    )
    assert actions[-1].action_type == "update_config"
    assert actions[-1].action_details["updated_fields"]["reminders_enabled"] is False


def test_authorization_required_for_state_change(session):
    user = _create_user(session, slack_user_id="UNAUTH")
    channel = _create_channel(session)
    actor = AdminActor(
        user_id=str(user.id),
        slack_user_id=user.slack_user_id,
        slack_roles=("member",),
    )
    service = AdminService(session, authorizer=SlackAdminAuthorizer())

    with pytest.raises(AdminAuthorizationError):
        service.set_channel_enabled(
            slack_channel_id=channel.slack_channel_id,
            actor=actor,
            enabled=False,
            reason="not allowed",
        )


def test_disable_channel_logs_reason(session):
    user = _create_user(session)
    channel = _create_channel(session)
    actor = AdminActor(
        user_id=str(user.id),
        slack_user_id=user.slack_user_id,
        slack_roles=("admin",),
    )
    service = AdminService(
        session,
        authorizer=SlackAdminAuthorizer(allowed_user_ids=[user.slack_user_id]),
    )

    result = service.set_channel_enabled(
        slack_channel_id=channel.slack_channel_id,
        actor=actor,
        enabled=False,
        reason="maintenance",
    )

    assert result.enabled is False
    refreshed = session.get(Channel, channel.id)
    assert refreshed.enabled is False

    action = (
        session.execute(
            select(ChannelAdminAction)
            .where(ChannelAdminAction.channel_id == channel.id)
            .order_by(ChannelAdminAction.created_at.desc())
        )
        .scalars()
        .first()
    )
    assert action is not None
    assert action.action_type == "disable"
    assert action.action_details["reason"] == "maintenance"


def test_reset_channel_data_clears_related_rows(session):
    user = _create_user(session)
    channel = _create_channel(session)
    _seed_run_with_related_records(session, channel, user)
    actor = AdminActor(
        user_id=str(user.id),
        slack_user_id=user.slack_user_id,
        slack_roles=("admin",),
    )
    service = AdminService(
        session,
        authorizer=SlackAdminAuthorizer(allowed_user_ids=[user.slack_user_id]),
    )

    result = service.reset_channel_data(
        slack_channel_id=channel.slack_channel_id,
        actor=actor,
    )

    assert result.orders_deleted == 1
    assert result.runs_deleted == 1
    assert result.preferences_deleted == 1
    assert result.runner_stats_deleted == 1

    assert (
        session.execute(select(Run).where(Run.channel_id == channel.id)).first() is None
    )
    assert (
        session.execute(select(Order).where(Order.run_id == result.channel_id)).first()
        is None
    )
    refreshed = session.get(Channel, channel.id)
    assert refreshed.last_reset_at is not None

    action = (
        session.execute(
            select(ChannelAdminAction)
            .where(ChannelAdminAction.channel_id == channel.id)
            .order_by(ChannelAdminAction.created_at.desc())
        )
        .scalars()
        .first()
    )
    assert action is not None
    assert action.action_type == "data_reset"
    assert action.action_details["orders_deleted"] == 1


def test_update_channel_config_validates_ranges(session):
    user = _create_user(session)
    channel = _create_channel(session)
    actor = AdminActor(
        user_id=str(user.id),
        slack_user_id=user.slack_user_id,
        slack_roles=("admin",),
    )
    service = AdminService(
        session,
        authorizer=SlackAdminAuthorizer(allowed_user_ids=[user.slack_user_id]),
    )
    patch = ChannelConfigPatch(reminder_offset_minutes=0)

    with pytest.raises(ChannelConfigValidationError):
        service.update_channel_config(
            slack_channel_id=channel.slack_channel_id,
            actor=actor,
            patch=patch,
        )


def _create_user(session, slack_user_id: str = "UADMIN") -> User:
    now = datetime.now(timezone.utc)
    user = User(
        id=uuid4(),
        slack_user_id=slack_user_id,
        display_name="Coffee Admin",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    session.add(user)
    session.flush()
    return user


def _create_channel(session, slack_channel_id: str = "CADMIN") -> Channel:
    now = datetime.now(timezone.utc)
    channel = Channel(
        id=uuid4(),
        slack_channel_id=slack_channel_id,
        name="coffee-pilot",
        enabled=True,
        reminder_offset_minutes=5,
        fairness_window_runs=5,
        data_retention_days=90,
        reminders_enabled=True,
        last_call_enabled=True,
        last_call_lead_minutes=5,
        last_reset_at=None,
        created_at=now,
        updated_at=now,
    )
    session.add(channel)
    session.flush()
    return channel


def _seed_run_with_related_records(session, channel: Channel, user: User) -> None:
    now = datetime.now(timezone.utc)
    run_kwargs = {
        "id": uuid4(),
        "channel_id": channel.id,
        "initiator_user_id": user.id,
        "runner_user_id": None,
        "status": RunStatus.OPEN.value,
        "pickup_time": None,
        "pickup_note": None,
        "started_at": now,
        "closed_at": None,
        "failure_reason": None,
        "created_at": now,
        "updated_at": now,
    }
    if hasattr(Run, "correlation_id"):
        run_kwargs["correlation_id"] = "corr-reset-test"
    run = Run(**run_kwargs)

    order = Order(
        id=uuid4(),
        run_id=run.id,
        user_id=user.id,
        order_text="Latte",
        is_final=True,
        provenance="manual",
        created_at=now,
        updated_at=now,
        canceled_at=None,
    )
    preference = UserPreference(
        id=uuid4(),
        user_id=user.id,
        channel_id=channel.id,
        last_order_text="Latte",
        last_used_at=now,
        created_at=now,
        updated_at=now,
    )
    stats = RunnerStat(
        id=uuid4(),
        user_id=user.id,
        channel_id=channel.id,
        runs_served_count=3,
        last_run_at=now,
        created_at=now,
        updated_at=now,
    )
    session.add_all([run, order, preference, stats])
    session.flush()