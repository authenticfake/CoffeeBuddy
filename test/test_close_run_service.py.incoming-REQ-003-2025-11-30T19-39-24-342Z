from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable, Iterable, Sequence
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from coffeebuddy.core.runs.models import CloseRunRequest
from coffeebuddy.core.runs.service import (
    CloseRunService,
    RunCloseAuthorizer,
    RunEventPublisher,
)
from coffeebuddy.core.runs.summary import RunSummaryBuilder
from coffeebuddy.infra.db.models import (
    Base,
    Channel,
    Order,
    Run,
    RunStatus,
    RunnerStat,
    User,
)
from coffeebuddy.infra.kafka.models import KafkaEvent
from coffeebuddy.services.fairness import FairnessSelector


@pytest.fixture(name="session")
def session_fixture() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)()


class AllowAllAuthorizer:
    def assert_can_close(self, *, run: Run, actor_user_id: str) -> None:
        return None


class RecordingPublisher:
    def __init__(self) -> None:
        self.events: list[KafkaEvent] = []

    def publish(self, *, topic: str, event: KafkaEvent) -> None:
        self.events.append(event)


def _seed_data(session: Session) -> tuple[Run, Channel, list[User]]:
    channel = Channel(
        id=str(uuid4()),
        slack_channel_id="C123",
        name="coffee",
        enabled=True,
        reminder_offset_minutes=5,
        fairness_window_runs=3,
        data_retention_days=90,
    )
    initiator = User(
        id=str(uuid4()),
        slack_user_id="U_INIT",
        display_name="Initiator",
        is_active=True,
    )
    runner_candidate = User(
        id=str(uuid4()),
        slack_user_id="U_RUN",
        display_name="Runner 1",
        is_active=True,
    )
    other_candidate = User(
        id=str(uuid4()),
        slack_user_id="U_OTHER",
        display_name="Runner 2",
        is_active=True,
    )
    session.add_all([channel, initiator, runner_candidate, other_candidate])
    session.commit()

    run = Run(
        id=str(uuid4()),
        channel_id=channel.id,
        initiator_user_id=initiator.id,
        status=RunStatus.OPEN,
        pickup_time=None,
        pickup_note=None,
        started_at=datetime.now(timezone.utc),
    )
    session.add(run)
    session.commit()

    order1 = Order(
        id=str(uuid4()),
        run_id=run.id,
        user_id=runner_candidate.id,
        order_text="Latte",
        provenance="manual",
        is_final=False,
    )
    order2 = Order(
        id=str(uuid4()),
        run_id=run.id,
        user_id=other_candidate.id,
        order_text="Espresso",
        provenance="manual",
        is_final=True,
    )
    session.add_all([order1, order2])
    session.commit()

    return run, channel, [initiator, runner_candidate, other_candidate]


def _build_service(session: Session) -> tuple[CloseRunService, RecordingPublisher]:
    fairness_selector = FairnessSelector(session)
    summary_builder = RunSummaryBuilder()
    authorizer: RunCloseAuthorizer = AllowAllAuthorizer()
    publisher = RecordingPublisher()
    service = CloseRunService(
        session=session,
        fairness_selector=fairness_selector,
        summary_builder=summary_builder,
        authorizer=authorizer,
        publisher=publisher,
    )
    return service, publisher


def test_close_run_assigns_runner_and_publishes_events(session: Session) -> None:
    run, channel, users = _seed_data(session)
    service, publisher = _build_service(session)

    result = service.close_run(
        CloseRunRequest(
            run_id=str(run.id),
            actor_user_id=str(users[0].id),
            correlation_id="corr-123",
        )
    )

    refreshed_run = session.get(Run, run.id)
    assert refreshed_run.status == RunStatus.CLOSED
    assert refreshed_run.runner_user_id == result.runner_user_id
    assert result.summary.participant_count == 2
    assert len(publisher.events) == 2
    runner_stat = (
        session.query(RunnerStat)
        .filter(
            RunnerStat.user_id == result.runner_user_id,
            RunnerStat.channel_id == channel.id,
        )
        .one()
    )
    assert runner_stat.runs_served_count == 1


def test_close_run_requires_open_status(session: Session) -> None:
    run, _, users = _seed_data(session)
    service, _ = _build_service(session)
    run.status = RunStatus.CLOSED
    session.commit()

    with pytest.raises(Exception):
        service.close_run(
            CloseRunRequest(
                run_id=str(run.id),
                actor_user_id=str(users[0].id),
                correlation_id="corr",
            )
        )