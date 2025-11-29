from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from coffeebuddy.core.orders.exceptions import (
    RunNotFoundError,
    RunNotOpenError,
    UserNotFoundError,
)
from coffeebuddy.core.orders.models import Clock, OrderProvenance
from coffeebuddy.infra.db.models import Order, Run, RunStatus, User


class OrderRepository:
    """Persistence helpers for order rows."""

    def __init__(self, session: Session, *, clock: Clock | None = None) -> None:
        self._session = session
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def upsert_order(
        self,
        *,
        run_id: str | UUID,
        user_id: str | UUID,
        order_text: str,
        confirm: bool,
        provenance: OrderProvenance,
    ) -> Order:
        order = self.get_order(run_id=run_id, user_id=user_id)
        now = self._clock()
        if order:
            order.order_text = order_text
            order.is_final = confirm
            order.provenance = provenance.value
            order.canceled_at = None
            order.updated_at = now
        else:
            order = Order(
                id=uuid4(),
                run_id=self._as_uuid(run_id),
                user_id=self._as_uuid(user_id),
                order_text=order_text,
                is_final=confirm,
                provenance=provenance.value,
                created_at=now,
                updated_at=now,
            )
            self._session.add(order)
        return order

    def get_order(self, *, run_id: str | UUID, user_id: str | UUID) -> Order | None:
        stmt = select(Order).where(
            Order.run_id == self._as_uuid(run_id),
            Order.user_id == self._as_uuid(user_id),
        )
        return self._session.scalar(stmt)

    def cancel_order(self, order: Order) -> Order:
        now = self._clock()
        order.canceled_at = now
        order.updated_at = now
        return order

    def count_active_orders(self, *, run_id: str | UUID) -> int:
        stmt = (
            select(func.count(Order.id))
            .where(Order.run_id == self._as_uuid(run_id), Order.canceled_at.is_(None))
        )
        return int(self._session.scalar(stmt) or 0)

    @staticmethod
    def _as_uuid(value: str | UUID) -> UUID:
        if isinstance(value, UUID):
            return value
        return UUID(value)


class RunRepository:
    """Lookup helpers for run metadata."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, run_id: str | UUID) -> Run:
        stmt = select(Run).where(Run.id == self._as_uuid(run_id))
        run = self._session.scalar(stmt)
        if not run:
            raise RunNotFoundError(f"Run {run_id} was not found.")
        return run

    def get_open_run(self, run_id: str | UUID) -> Run:
        run = self.get(run_id)
        if run.status != RunStatus.OPEN:
            raise RunNotOpenError(f"Run {run_id} is not open for orders.")
        return run

    @staticmethod
    def _as_uuid(value: str | UUID) -> UUID:
        if isinstance(value, UUID):
            return value
        return UUID(value)


class UserRepository:
    """Lookup helpers for Slack users."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, user_id: str | UUID) -> User:
        user = self._session.get(User, self._as_uuid(user_id))
        if not user:
            raise UserNotFoundError(f"User {user_id} does not exist.")
        return user

    @staticmethod
    def _as_uuid(value: str | UUID) -> UUID:
        if isinstance(value, UUID):
            return value
        return UUID(value)