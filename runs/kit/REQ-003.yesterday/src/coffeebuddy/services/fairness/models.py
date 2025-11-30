from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FairnessDecision:
    """Outcome from the fairness selector."""

    runner_user_id: str
    rationale: str