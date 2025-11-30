from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from coffeebuddy.infra.db.models import Base, Channel, Run, RunStatus, User
from coffeebuddy.services.fairness import FairnessSelector
from coffeebuddy.core.runs import exceptions as run_exc


@pytest.fixture(name="session")
def session_fixture() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)()


def _seed_channel_and_users(session: Session) -> tuple[Channel, list[User]]:
    channel = Channel(
        id=str(uuid4()),
        slack_channel_id="C123",
        name="coffee",
        enabled=True,
        reminder_offset_minutes=5,
        fairness_window_runs=3,
        data_retention_days=90,
    )
    users = [
        User(
            id=str(uuid4()),
            slack_user_id=f"U{i}",
            display_name=f"User {i}",
            is_active=True,
        )
        for i in range(3)
    ]
    session.add(channel)
    session.add_all(users)
    session.commit()
    return channel, users


def _add_closed_run(
    session: Session, *, channel_id: str, runner_id: str, hours_ago: int
) -> None:
    now = datetime.now(timezone.utc)
    run = Run(
        id=str(uuid4()),
        channel_id=channel_id,
        initiator_user_id=runner_id,
        runner_user_id=runner_id,
        status=RunStatus.CLOSED,
        pickup_time=None,
        pickup_note=None,
        started_at=now - timedelta(hours=hours_ago + 1),
        closed_at=now - timedelta(hours=hours_ago),
    )
    session.add(run)
    session.commit()


def test_selector_prefers_lowest_recent_count(session: Session) -> None:
    channel, users = _seed_channel_and_users(session)
    # user0 served twice recently, user1 once, user2 never
    _add_closed_run(session, channel_id=channel.id, runner_id=users[0].id, hours_ago=1)
    _add_closed_run(session, channel_id=channel.id, runner_id=users[0].id, hours_ago=2)
    _add_closed_run(session, channel_id=channel.id, runner_id=users[1].id, hours_ago=3)

    selector = FairnessSelector(session)

    result = selector.select_runner(
        channel_id=str(channel.id),
        candidate_user_ids=[str(u.id) for u in users],
        fairness_window_runs=3,
    )

    assert result.runner_user_id == str(users[2].id)
    assert "served 0x" in result.explanation


def test_selector_avoids_consecutive_runner_when_possible(session: Session) -> None:
    channel, users = _seed_channel_and_users(session)
    _add_closed_run(session, channel_id=channel.id, runner_id=users[1].id, hours_ago=1)

    selector = FairnessSelector(session)

    result = selector.select_runner(
        channel_id=str(channel.id),
        candidate_user_ids=[str(u.id) for u in users[1:]],
        fairness_window_runs=2,
    )

    assert result.runner_user_id == str(users[2].id)


def test_selector_allows_consecutive_when_only_option(session: Session) -> None:
    channel, users = _seed_channel_and_users(session)
    _add_closed_run(session, channel_id=channel.id, runner_id=users[0].id, hours_ago=1)

    selector = FairnessSelector(session)

    result = selector.select_runner(
        channel_id=str(channel.id),
        candidate_user_ids=[str(users[0].id)],
        fairness_window_runs=2,
    )

    assert result.runner_user_id == str(users[0].id)
    assert "consecutive" in result.explanation.lower()


def test_selector_errors_when_no_candidates(session: Session) -> None:
    selector = FairnessSelector(session)
    with pytest.raises(run_exc.NoEligibleRunnerError):
        selector.select_runner(
            channel_id="cid",
            candidate_user_ids=[],
            fairness_window_runs=2,
        )