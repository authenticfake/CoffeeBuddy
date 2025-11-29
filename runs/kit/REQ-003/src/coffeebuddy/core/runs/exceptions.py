from __future__ import annotations


class RunCloseError(Exception):
    """Base error for run lifecycle operations."""


class RunNotFoundError(RunCloseError):
    """Raised when the requested run identifier cannot be resolved."""


class RunNotOpenError(RunCloseError):
    """Raised when a run is not in an open state when an action requires it."""


class UnauthorizedRunCloseError(RunCloseError):
    """Raised when an actor attempts to close a run without required privileges."""


class RunnerSelectionError(RunCloseError):
    """Raised when a runner cannot be chosen according to fairness criteria."""