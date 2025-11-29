from __future__ import annotations

from collections.abc import Callable
from contextlib import contextmanager
from typing import Iterator, Protocol

from sqlalchemy.orm import Session

from coffeebuddy.config import Settings
from coffeebuddy.events.run import RunEventPublisher


class _SlackRunDependencyState:
    settings: Settings | None = None
    session_factory: Callable[[], Session] | None = None
    event_publisher: RunEventPublisher | None = None


_state = _SlackRunDependencyState()


def configure_dependencies(
    *,
    settings: Settings,
    session_factory: Callable[[], Session],
    event_publisher: RunEventPublisher,
) -> None:
    _state.settings = settings
    _state.session_factory = session_factory
    _state.event_publisher = event_publisher


def get_settings() -> Settings:
    if not _state.settings:
        raise RuntimeError("Slack run dependencies not configured")
    return _state.settings


@contextmanager
def _session_manager() -> Iterator[Session]:
    if not _state.session_factory:
        raise RuntimeError("Session factory not configured")
    session = _state.session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_session() -> Iterator[Session]:
    with _session_manager() as session:
        yield session


def get_run_event_publisher() -> RunEventPublisher:
    if not _state.event_publisher:
        raise RuntimeError("Run event publisher not configured")
    return _state.event_publisher


class RouterProtocol(Protocol):
    dependencies: list
    def copy(self) -> "RouterProtocol": ...
    def add_api_route(self, *args, **kwargs): ...


def get_router_with_dependencies(router: RouterProtocol):
    router.dependencies = []
    return router