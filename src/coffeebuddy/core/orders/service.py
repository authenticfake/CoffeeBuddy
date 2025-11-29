from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable

from sqlalchemy.orm import Session

from coffeebuddy.core.orders.exceptions import (
    OrderNotFoundError,
    OrderValidationError,
    PreferenceNotFoundError,
    RunNotFoundError,
    RunNotOpenError,
    UserNotFoundError,
)
from coffeebuddy.core.orders.models import (
    Clock,
    OrderCancellationResult,
    OrderProvenance,
    OrderSubmissionRequest,
    OrderSubmissionResult,
    UseLastOrderResult,
)
from coffeebuddy.core.orders.repository import (
    OrderRepository,
    RunRepository,
    UserRepository,
)
from coffeebuddy.infra.db.models import Run, User
from coffeebuddy.services.preferences import PreferenceService


class OrderValidator:
    """Validates free-form order text."""

    def __init__(self, *, max_length: int = 280) -> None:
        self._max_length = max_length

    def validate(self, order_text: str) -> str:
        normalized = order_text.strip()
        if not normalized:
            raise OrderValidationError("Order cannot be empty.")
        if len(normalized) > self._max_length:
            raise OrderValidationError(
                f"Order length exceeds {self._max_length} characters."
            )
        return normalized


class OrderService:
    """Provides core order capture, edits, preference reuse and cancellation."""

    def __init__(
        self,
        session: Session,
        *,
        clock: Clock | None = None,
        validator: OrderValidator | None = None,
        preference_service: PreferenceService | None = None,
        order_repository_factory: Callable[[Session], OrderRepository] | None = None,
    ) -> None:
        self._session = session
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._validator = validator or OrderValidator()
        self._orders = (
            order_repository_factory(session)
            if order_repository_factory
            else OrderRepository(session, clock=self._clock)
        )
        self._runs = RunRepository(session)
        self._users = UserRepository(session)
        self._preferences = preference_service or PreferenceService(
            session, clock=self._clock
        )

    def submit_order(self, request: OrderSubmissionRequest) -> OrderSubmissionResult:
        try:
            run = self._runs.get_open_run(request.run_id)
        except RunNotFoundError:
            raise
        except RunNotOpenError:
            raise
        user = self._users.get(request.user_id)
        normalized = self._validator.validate(request.order_text)
        return self._persist_order(
            run=run,
            user=user,
            order_text=normalized,
            confirm=request.confirm,
            provenance=request.provenance,
        )

    def use_last_order(self, *, run_id: str, user_id: str) -> UseLastOrderResult:
        run = self._runs.get_open_run(run_id)
        user = self._users.get(user_id)
        preference = self._preferences.get_preference(
            user_id=user.id, channel_id=run.channel_id
        )
        if not preference:
            raise PreferenceNotFoundError(
                f"No saved order found for user {user_id} in this channel."
            )
        normalized = self._validator.validate(preference.last_order_text)
        submission = self._persist_order(
            run=run,
            user=user,
            order_text=normalized,
            confirm=True,
            provenance=OrderProvenance.PREFERENCE,
        )
        self._preferences.mark_used(preference)
        return UseLastOrderResult(
            preference_id=str(preference.id),
            submission=submission,
        )

    def cancel_order(self, *, run_id: str, user_id: str) -> OrderCancellationResult:
        run = self._runs.get_open_run(run_id)
        _ = self._users.get(user_id)
        order = self._orders.get_order(run_id=run.id, user_id=user_id)
        if not order or order.canceled_at is not None:
            raise OrderNotFoundError(
                f"No active order for user {user_id} in run {run_id}."
            )
        self._orders.cancel_order(order)
        participant_count = self._orders.count_active_orders(run_id=run.id)
        return OrderCancellationResult(
            order_id=str(order.id),
            participant_count=participant_count,
        )

    def _persist_order(
        self,
        *,
        run: Run,
        user: User,
        order_text: str,
        confirm: bool,
        provenance: OrderProvenance,
    ) -> OrderSubmissionResult:
        order = self._orders.upsert_order(
            run_id=run.id,
            user_id=user.id,
            order_text=order_text,
            confirm=confirm,
            provenance=provenance,
        )
        preference_updated = False
        if confirm:
            self._preferences.set_preference(
                user_id=user.id,
                channel_id=run.channel_id,
                order_text=order.order_text,
            )
            preference_updated = True
        participant_count = self._orders.count_active_orders(run_id=run.id)
        return OrderSubmissionResult(
            order_id=str(order.id),
            participant_count=participant_count,
            order_text=order.order_text,
            provenance=provenance,
            preference_updated=preference_updated,
        )