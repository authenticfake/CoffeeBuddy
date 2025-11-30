"""Domain-specific errors for the run lifecycle."""

class RunNotFoundError(Exception):
    """Raised when the requested run does not exist."""


class RunAlreadyClosedError(Exception):
    """Raised when attempting to close a non-open run."""


class UnauthorizedRunClosureError(Exception):
    """Raised when the actor lacks permission to close the run."""


class ChannelDisabledError(Exception):
    """Raised when the channel is disabled for CoffeeBuddy operations."""


class NoEligibleRunnerError(Exception):
    """Raised when the fairness algorithm cannot find a runner."""