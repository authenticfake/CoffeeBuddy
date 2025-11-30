from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from typing import Sequence

from sqlalchemy import Select, desc, select
from sqlalchemy.orm import Session

from coffeebuddy.core.runs import exceptions as run_exc
from coffeebuddy.infra.db.models import Run, RunStatus


@dataclass(frozen=True, slots=True)
class RunnerSelection:
    """Outcome of fairness evaluation."""

    runner_user_id: str
    explanation: str


class FairnessSelector:
    """Deterministic runner selection using channel history."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def select_runner(
        self,
        *,
        channel_id: str,
        candidate_user_ids: Sequence[str],
        fairness_window_runs: int,
        allow_immediate_repeat: bool = False,
    ) -> RunnerSelection:
        if not candidate_user_ids:
            raise run_exc.NoEligibleRunnerError("No participating users provided.")

        window = max(1, fairness_window_runs)
        history = self._fetch_recent_history(channel_id=channel_id, limit=window)
        counts = Counter(r.runner_user_id for r in history if r.runner_user_id)
        previous_runner_id = next(
            (r.runner_user_id for r in history if r.runner_user_id), None
        )

        eligible = list(dict.fromkeys(candidate_user_ids))  # preserve order
        if (
            not allow_immediate_repeat
            and previous_runner_id in eligible
            and len(eligible) > 1
        ):
            eligible = [uid for uid in eligible if uid != previous_runner_id]

        if not eligible:
            # Fallback to previous runner when they are the sole participant.
            eligible = [previous_runner_id] if previous_runner_id else []

        if not eligible:
            raise run_exc.NoEligibleRunnerError("Fairness selector found no runner.")

        def last_served_at(user_id: str) -> datetime | None:
            for record in history:
                if record.runner_user_id == user_id:
                    return record.closed_at
            return None

        def sort_key(user_id: str) -> tuple[int, datetime | None, str]:
            served_count = counts.get(user_id, 0)
            served_at = last_served_at(user_id)
            return (served_count, served_at or datetime.min, user_id)

        selected_user_id = sorted(eligible, key=sort_key)[0]
        explanation = self._build_explanation(
            selected_user_id=selected_user_id,
            counts=counts,
            fairness_window=window,
            previous_runner_id=previous_runner_id,
        )
        return RunnerSelection(
            runner_user_id=selected_user_id,
            explanation=explanation,
        )

    def _fetch_recent_history(
        self, *, channel_id: str, limit: int
    ) -> list[RunHistoryRecord]:
        query: Select[tuple[str | None, datetime | None]] = (
            select(Run.runner_user_id, Run.closed_at)
            .where(
                Run.channel_id == channel_id,
                Run.status == RunStatus.CLOSED,
                Run.runner_user_id.is_not(None),
            )
            .order_by(desc(Run.closed_at))
            .limit(limit)
        )
        rows = self._session.execute(query).all()
        return [
            RunHistoryRecord(runner_user_id=row[0], closed_at=row[1]) for row in rows
        ]

    def _build_explanation(
        self,
        *,
        selected_user_id: str,
        counts: Counter,
        fairness_window: int,
        previous_runner_id: str | None,
    ) -> str:
        run_count = counts.get(selected_user_id, 0)
        base = (
            f"Runner chosen based on lowest assignments in last {fairness_window} runs "
            f"(served {run_count}x)."
        )
        if previous_runner_id == selected_user_id:
            return base + " Only eligible participant; consecutive assignment allowed."
        return base


@dataclass(frozen=True, slots=True)
class RunHistoryRecord:
    runner_user_id: str | None
    closed_at: datetime | None