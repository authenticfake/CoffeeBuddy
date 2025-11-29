from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from coffeebuddy.core.orders import OrderService
from coffeebuddy.core.orders.exceptions import (
    OrderNotFoundError,
    OrderValidationError,
    PreferenceNotFoundError,
)
from coffeebuddy.core.orders.models import OrderProvenance, OrderSubmissionRequest
from coffeebuddy.infra.db.models import (
    Base,
    Channel,
    Order,
    Run,
    RunStatus,
    User,
    UserPreference,
)


@pytest.fixture()
def ticking_clock():
    current = datetime(2024, 1, 1, tzinfo=timezone.utc)

    def _tick():
        nonlocal current
        value = current
        current = current + timedelta(seconds=1)
        return value

    return _tick


@pytest.fixture()
def session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture()
def seeded_entities(session: Session) -> SimpleNamespace:
    now = datetime(2024, 1, 1, tzinfo=timezone.utc)
    channel = Channel(
        id=uuid4(),
        slack_channel_id="C123",
        name="coffee",
        enabled=True,
        reminder_offset_minutes=5,
        fairness_window_runs=5,
        data_retention_days=90,
        reminders_enabled=True,
        last_call_enabled=True,
        created_at=now,
        updated_at=now,
    )
    user = User(
        id=uuid4(),
        slack_user_id="U123",
        display_name="Coffee Tester",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    run = Run(
        id=uuid4(),
        channel_id=channel.id,
        initiator_user_id=user.id,
        status=RunStatus.OPEN,
        pickup_time=None,
        pickup_note=None,
        runner_user_id=None,
        started_at=now,
        closed_at=None,
        failure_reason=None,
        created_at=now,
        updated_at=now,
    )
    session.add_all([channel, user, run])
    session.commit()
    return SimpleNamespace(channel=channel, user=user, run=run)


def _create_run(session: Session, channel: Channel, user: User) -> Run:
    now = datetime(2024, 1, 2, tzinfo=timezone.utc)
    run = Run(
        id=uuid4(),
        channel_id=channel.id,
        initiator_user_id=user.id,
        status=RunStatus.OPEN,
        pickup_time=None,
        pickup_note=None,
        runner_user_id=None,
        started_at=now,
        closed_at=None,
        failure_reason=None,
        created_at=now,
        updated_at=now,
    )
    session.add(run)
    session.commit()
    return run


def test_submit_order_creates_row_and_preference(
    session: Session, seeded_entities: SimpleNamespace, ticking_clock
):
    service = OrderService(session, clock=ticking_clock)
    request = OrderSubmissionRequest(
        run_id=str(seeded_entities.run.id),
        user_id=str(seeded_entities.user.id),
        order_text="Flat white",
    )

    result = service.submit_order(request)

    assert result.participant_count == 1
    assert result.preference_updated is True
    pref_stmt = select(UserPreference).where(
        UserPreference.user_id == seeded_entities.user.id,
        UserPreference.channel_id == seeded_entities.channel.id,
    )
    preference = session.scalar(pref_stmt)
    assert preference is not None
    assert preference.last_order_text == "Flat white"


def test_submit_order_updates_existing_entry(
    session: Session, seeded_entities: SimpleNamespace, ticking_clock
):
    service = OrderService(session, clock=ticking_clock)
    base_request = OrderSubmissionRequest(
        run_id=str(seeded_entities.run.id),
        user_id=str(seeded_entities.user.id),
        order_text="Latte",
    )
    first = service.submit_order(base_request)

    updated = service.submit_order(
        OrderSubmissionRequest(
            run_id=str(seeded_entities.run.id),
            user_id=str(seeded_entities.user.id),
            order_text="Oat latte",
            provenance=OrderProvenance.EDIT,
        )
    )

    assert first.order_id == updated.order_id
    orders = session.scalars(
        select(Order).where(Order.run_id == seeded_entities.run.id)
    ).all()
    assert len(orders) == 1
    assert orders[0].order_text == "Oat latte"
    assert updated.participant_count == 1


def test_use_last_order_replays_preference_into_new_run(
    session: Session, seeded_entities: SimpleNamespace, ticking_clock
):
    service = OrderService(session, clock=ticking_clock)
    service.submit_order(
        OrderSubmissionRequest(
            run_id=str(seeded_entities.run.id),
            user_id=str(seeded_entities.user.id),
            order_text="Americano",
        )
    )
    new_run = _create_run(session, seeded_entities.channel, seeded_entities.user)

    reuse_result = service.use_last_order(
        run_id=str(new_run.id), user_id=str(seeded_entities.user.id)
    )

    assert reuse_result.submission.participant_count == 1
    assert reuse_result.submission.order_text == "Americano"
    preference = session.scalar(
        select(UserPreference).where(
            UserPreference.user_id == seeded_entities.user.id,
            UserPreference.channel_id == seeded_entities.channel.id,
        )
    )
    assert preference is not None
    assert preference.last_used_at is not None


def test_use_last_order_without_preference_fails(
    session: Session, seeded_entities: SimpleNamespace, ticking_clock
):
    service = OrderService(session, clock=ticking_clock)
    new_run = _create_run(session, seeded_entities.channel, seeded_entities.user)

    with pytest.raises(PreferenceNotFoundError):
        service.use_last_order(
            run_id=str(new_run.id), user_id=str(seeded_entities.user.id)
        )


def test_cancel_order_marks_row_and_updates_count(
    session: Session, seeded_entities: SimpleNamespace, ticking_clock
):
    service = OrderService(session, clock=ticking_clock)
    submission = service.submit_order(
        OrderSubmissionRequest(
            run_id=str(seeded_entities.run.id),
            user_id=str(seeded_entities.user.id),
            order_text="Mocha",
        )
    )
    assert submission.participant_count == 1

    cancellation = service.cancel_order(
        run_id=str(seeded_entities.run.id), user_id=str(seeded_entities.user.id)
    )

    assert cancellation.participant_count == 0
    order = session.scalar(
        select(Order).where(
            Order.run_id == seeded_entities.run.id,
            Order.user_id == seeded_entities.user.id,
        )
    )
    assert order is not None
    assert order.canceled_at is not None


def test_cancel_missing_order_errors(
    session: Session, seeded_entities: SimpleNamespace, ticking_clock
):
    service = OrderService(session, clock=ticking_clock)

    with pytest.raises(OrderNotFoundError):
        service.cancel_order(
            run_id=str(seeded_entities.run.id), user_id=str(seeded_entities.user.id)
        )


def test_blank_orders_are_rejected(
    session: Session, seeded_entities: SimpleNamespace, ticking_clock
):
    service = OrderService(session, clock=ticking_clock)

    with pytest.raises(OrderValidationError):
        service.submit_order(
            OrderSubmissionRequest(
                run_id=str(seeded_entities.run.id),
                user_id=str(seeded_entities.user.id),
                order_text="   ",
            )
        )