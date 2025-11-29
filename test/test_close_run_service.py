from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from coffeebuddy.core.runs.exceptions import (
    RunnerSelectionError,
    UnauthorizedRunCloseError,
)
from coffeebuddy.core.runs.models import CloseRunRequest
from coffeebuddy.core.runs.service import CloseRunAuthorizer, CloseRunService
from coffeebuddy.infra.db.models import (
    Base,
    Channel,
    Order,
    Run,
    RunStatus,
    RunnerStat,
    User,
)
from coffeebuddy.services.fairness.service import FairnessService


@pytest.fixture()
def session():
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    sess = Session()
    try:
        yield sess
    finally:
        sess.close()
        engine.dispose()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class InitiatorOnlyAuthorizer:
    """Simple authorizer that allows only the run initiator to close a run."""

    def is_authorized(self, *, run: Run, actor_user_id: str) -> bool:
        return str(run.initiator_user_id) == actor_user_id


def _create_user(session, slack_id: str, display_name: str) -> User:
    now = _utcnow()
    user = User(
        id=uuid4(),
        slack_user_id=slack_id,
        display_name=display_name,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    session.add(user)
    session.commit()
    return user


def _create_channel(session) -> Channel:
    now = _utcnow()
    channel = Channel(
        id=uuid4(),
        slack_channel_id="C123TEST",
        name="coffee-test",
        enabled=True,
        reminder_offset_minutes=5,
        fairness_window_runs=5,
        data_retention_days=90,
        reminders_enabled=True,
        last_call_enabled=True,
        last_call_lead_minutes=None,
        created_at=now,
        updated_at=now,
    )
    session.add(channel)
    session.commit()
    return channel


def _create_run(session, channel: Channel, initiator: User) -> Run:
    now = _utcnow()
    run = Run(
        id=uuid4(),
        channel_id=channel.id,
        initiator_user_id=initiator.id,
        runner_user_id=None,
        status=RunStatus.OPEN,
        pickup_time=now + timedelta(minutes=30),
        pickup_note="Lobby cafe",
        started_at=now,
        closed_at=None,
        failure_reason=None,
        created_at=now,
        updated_at=now,
    )
    session.add(run)
    session.commit()
    return run


def _create_order(session, run: Run, user: User, text: str) -> Order:
    now = _utcnow()
    order = Order(
        id=uuid4(),
        run_id=run.id,
        user_id=user.id,
        order_text=text,
        is_final=False,
        provenance="manual",
        created_at=now,
        updated_at=now,
        canceled_at=None,
    )
    session.add(order)
    session.commit()
    return order


def _prime_runner_stat(session, channel: Channel, user: User, runs: int) -> RunnerStat:
    now = _utcnow()
    stat = RunnerStat(
        id=uuid4(),
        channel_id=channel.id,
        user_id=user.id,
        runs_served_count=runs,
        last_run_at=now - timedelta(days=1),
        created_at=now - timedelta(days=2),
        updated_at=now - timedelta(days=1),
    )
    session.add(stat)
    session.commit()
    return stat


def _create_previous_closed_run(
    session, channel: Channel, initiator: User, runner: User
) -> None:
    now = _utcnow()
    previous = Run(
        id=uuid4(),
        channel_id=channel.id,
        initiator_user_id=initiator.id,
        runner_user_id=runner.id,
        status=RunStatus.CLOSED,
        pickup_time=now - timedelta(hours=2),
        pickup_note="Previous spot",
        started_at=now - timedelta(hours=3),
        closed_at=now - timedelta(hours=2),
        failure_reason=None,
        created_at=now - timedelta(hours=3),
        updated_at=now - timedelta(hours=2),
    )
    session.add(previous)
    session.commit()


def test_close_run_service_closes_and_summarizes(session):
    channel = _create_channel(session)
    initiator = _create_user(session, "U100", "Initiator")
    participant_a = _create_user(session, "U101", "Alex")
    participant_b = _create_user(session, "U102", "Bailey")

    run = _create_run(session, channel, initiator)
    _create_previous_closed_run(session, channel, initiator, participant_a)
    _prime_runner_stat(session, channel, participant_a, runs=2)

    _create_order(session, run, participant_a, "Latte")
    _create_order(session, run, participant_b, "Mocha")

    fairness = FairnessService(session=session, clock=_utcnow)
    service = CloseRunService(
        session=session,
        fairness=fairness,
        authorizer=InitiatorOnlyAuthorizer(),
        clock=_utcnow,
    )

    result = service.close_run(
        CloseRunRequest(run_id=str(run.id), actor_user_id=str(initiator.id))
    )

    session.refresh(run)
    assert run.status == RunStatus.CLOSED
    assert result.runner_user_id == str(participant_b.id)
    assert result.summary.total_orders == 2
    assert any(p.display_name == "Bailey" for p in result.summary.participants)
    assert "Runner chosen" in result.fairness_note

    orders = session.execute(
        select(Order).where(Order.run_id == run.id)
    ).scalars().all()
    assert all(order.is_final for order in orders)


def test_close_run_rejects_unauthorized_actor(session):
    channel = _create_channel(session)
    initiator = _create_user(session, "U200", "Initiator")
    other_user = _create_user(session, "U201", "Other")

    run = _create_run(session, channel, initiator)
    _create_order(session, run, other_user, "Cold brew")

    fairness = FairnessService(session=session, clock=_utcnow)
    service = CloseRunService(
        session=session,
        fairness=fairness,
        authorizer=InitiatorOnlyAuthorizer(),
        clock=_utcnow,
    )

    with pytest.raises(UnauthorizedRunCloseError):
        service.close_run(
            CloseRunRequest(run_id=str(run.id), actor_user_id=str(other_user.id))
        )


def test_close_run_without_orders_raises(session):
    channel = _create_channel(session)
    initiator = _create_user(session, "U300", "Initiator")
    run = _create_run(session, channel, initiator)

    fairness = FairnessService(session=session, clock=_utcnow)
    service = CloseRunService(
        session=session,
        fairness=fairness,
        authorizer=InitiatorOnlyAuthorizer(),
        clock=_utcnow,
    )

    with pytest.raises(RunnerSelectionError):
        service.close_run(
            CloseRunRequest(run_id=str(run.id), actor_user_id=str(initiator.id))
        )