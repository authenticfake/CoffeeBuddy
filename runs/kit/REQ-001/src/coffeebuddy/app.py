from __future__ import annotations

from fastapi import FastAPI

from coffeebuddy.api.slack_runs import router as slack_router
from coffeebuddy.api.slack_runs.dependencies import (
    configure_dependencies,
    get_router_with_dependencies,
)
from coffeebuddy.config import Settings, get_settings
from coffeebuddy.infra.db import build_session_factory
from coffeebuddy.infra.kafka import KafkaRunEventPublisher


def create_app(
    *,
    settings: Settings | None = None,
    session_factory=None,
    event_publisher=None,
) -> FastAPI:
    app_settings = settings or get_settings()

    session_factory = session_factory or build_session_factory(app_settings.database_url)
    event_publisher = event_publisher or KafkaRunEventPublisher(
        bootstrap_servers=app_settings.kafka_bootstrap_servers,
        topic=app_settings.run_events_topic,
    )

    configure_dependencies(
        settings=app_settings,
        session_factory=session_factory,
        event_publisher=event_publisher,
    )

    app = FastAPI(title="CoffeeBuddy")
    app.include_router(
        get_router_with_dependencies(slack_router.router),
        prefix="",
    )
    return app


app = create_app()


__all__ = ["app", "create_app"]