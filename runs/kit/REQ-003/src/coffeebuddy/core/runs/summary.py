from __future__ import annotations

from coffeebuddy.core.runs.models import OrderSnapshot, RunSummary, RunnerSnapshot


class RunSummaryBuilder:
    """Creates deterministic run summaries for Slack messaging & auditing."""

    def build(
        self,
        *,
        run_id: str,
        channel_id: str,
        channel_name: str,
        pickup_time,
        pickup_note,
        runner: RunnerSnapshot,
        participant_orders: list[OrderSnapshot] | tuple[OrderSnapshot, ...],
        reminder_offset_minutes: int,
        fairness_explanation: str,
    ) -> RunSummary:
        orders = tuple(sorted(participant_orders, key=lambda o: (o.submitted_at, o.user_id)))
        return RunSummary(
            run_id=run_id,
            channel_id=channel_id,
            channel_name=channel_name,
            pickup_time=pickup_time,
            pickup_note=pickup_note,
            runner=runner,
            participant_orders=orders,
            participant_count=len(orders),
            reminder_offset_minutes=reminder_offset_minutes,
            fairness_explanation=fairness_explanation,
        )