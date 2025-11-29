from __future__ import annotations


class OrderError(Exception):
    """Base class for order related failures."""


class OrderValidationError(OrderError):
    """Raised when order text violates validation rules."""

    def __init__(self, message: str, *, field: str = "order_text") -> None:
        self.field = field
        super().__init__(message)


class RunNotFoundError(OrderError):
    """Raised when a run identifier cannot be resolved."""


class RunNotOpenError(OrderError):
    """Raised when a run is not accepting orders."""


class PreferenceNotFoundError(OrderError):
    """Raised when a user attempts to re-use a non-existent preference."""


class OrderNotFoundError(OrderError):
    """Raised when an expected order row is missing."""


class UserNotFoundError(OrderError):
    """Raised when the referenced user is missing in persistence."""