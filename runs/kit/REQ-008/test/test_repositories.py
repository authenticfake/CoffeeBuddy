from __future__ import annotations

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

import pytest

from coffeebuddy.infrastructure.db.models import Base, RunStatus
from coffeebuddy.infrastructure.db.repositories import (
    ChannelRepository,
    ChannelSettingsPatch,
    OrderRepository,
    RunRepository,
    UserPreferenceRepository,
    UserRepository,
)


@pytest.fixture()
def session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, future=True)
    with SessionLocal() as session:
        session.execute(text("PRAGMA foreign_keys=ON"))
        yield session


def test_user_repository_upsert_updates_name(session: Session) -> None:
    repo = UserRepository(session=session)
    user = repo.upsert(slack_user_id="U123", display_name="First Name")
    session.flush()
    assert user.display_name == "First Name"

    user = repo.upsert(slack_user_id="U123", display_name="Second Name")
    session.flush()
    assert user.display_name == "Second Name"


def test_run_repository_prevents_reopen(session: Session) -> None:
    user_repo = UserRepository(session=session)
    channel_repo = ChannelRepository(session=session)
    run_repo = RunRepository(session=session)

    user = user_repo.upsert(slack_user_id="U1", display_name="User")
    channel = channel_repo.upsert(slack_channel_id="C1", name="channel")
    run = run_repo.create(
        channel_id=channel.id,
        initiator_user_id=user.id,
        pickup_time=None,
        pickup_note=None,
    )
    session.flush()

    run_repo.update_status(run, RunStatus.CLOSED)
    session.flush()

    with pytest.raises(ValueError):
        run_repo.update_status(run, RunStatus.OPEN)


def test_order_repository_single_active_order(session: Session) -> None:
    user_repo = UserRepository(session=session)
    channel_repo = ChannelRepository(session=session)
    run_repo = RunRepository(session=session)
    order_repo = OrderRepository(session=session)
    prefs_repo = UserPreferenceRepository(session=session)

    user = user_repo.upsert(slack_user_id="UABC", display_name="Person")
    channel = channel_repo.upsert(slack_channel_id="CABCD", name="coffee")
    run = run_repo.create(
        channel_id=channel.id,
        initiator_user_id=user.id,
        pickup_time=None,
        pickup_note=None,
    )
    session.flush()

    order1 = order_repo.upsert_order(
        run_id=run.id,
        user_id=user.id,
        order_text="Latte",
        is_final=False,
    )
    session.flush()
    assert order1.order_text == "Latte"

    order2 = order_repo.upsert_order(
        run_id=run.id,
        user_id=user.id,
        order_text="Cappuccino",
        is_final=True,
    )
    session.flush()
    assert order2.id == order1.id
    assert order2.order_text == "Cappuccino"
    assert order2.is_final is True

    prefs_repo.save_preference(user_id=user.id, channel_id=channel.id, order_text="Cappuccino")
    session.flush()

    active = order_repo.list_active_orders(run_id=run.id)
    assert len(active) == 1
    assert active[0].order_text == "Cappuccino"


def test_channel_patch_updates_only_fields(session: Session) -> None:
    channel_repo = ChannelRepository(session=session)
    channel = channel_repo.upsert(slack_channel_id="C123", name="coffee-run")
    session.flush()

    patch = ChannelSettingsPatch(reminder_offset_minutes=7, reminders_enabled=False)
    channel_repo.update_settings(channel, patch)
    session.flush()

    refreshed = channel_repo.get_by_slack_id("C123")
    assert refreshed is not None
    assert refreshed.reminder_offset_minutes == 7
    assert refreshed.reminders_enabled is False
    assert refreshed.fairness_window_runs == 5