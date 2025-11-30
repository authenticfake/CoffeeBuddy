from __future__ import annotations

import uuid
from typing import Optional

from fastapi import FastAPI, Response, status
from fastapi.responses import JSONResponse
from prometheus_client import (
    CollectorRegistry,
    CONTENT_TYPE_LATEST,
    Gauge,
    PlatformCollector,
    ProcessCollector,
    generate_latest,
    multiprocess,
)
from starlette.requests import Request

from .config import ServiceConfig
from .probes import ReadinessRegistry


def build_metrics_registry(config: ServiceConfig) -> CollectorRegistry:
    registry = CollectorRegistry()
    if config.metrics.multiprocess_dir:
        multiprocess.MultiProcessCollector(registry)
    elif config.metrics.enable_default_process_metrics:
        ProcessCollector(registry=registry)
        PlatformCollector(registry=registry)
    return registry


def create_app(
    config: ServiceConfig,
    readiness_registry: Optional[ReadinessRegistry] = None,
    registry: Optional[CollectorRegistry] = None,
) -> FastAPI:
    readiness_registry = readiness_registry or ReadinessRegistry()
    registry = registry or build_metrics_registry(config)

    app = FastAPI(
        title="CoffeeBuddy Runtime",
        description="Runtime entrypoint for Slack + platform integrations.",
        version=config.version,
        debug=config.debug_enabled,
    )

    app.state.config = config
    app.state.readiness = readiness_registry
    app.state.registry = registry

    service_info = Gauge(
        "coffeebuddy_service_info",
        "Static info about the CoffeeBuddy service",
        ["environment", "version"],
        registry=registry,
    )
    service_info.labels(config.environment, config.version).set(1)

    @app.middleware("http")
    async def correlation_middleware(request: Request, call_next):
        correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
        request.state.correlation_id = correlation_id
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id
        return response

    @app.get("/health/live")
    async def liveness() -> dict:
        return {
            "status": "alive",
            "service": config.service_name,
            "version": config.version,
            "environment": config.environment,
        }

    @app.get("/health/ready")
    async def readiness():
        ready, results = await app.state.readiness.evaluate()
        payload = {
            "status": "ready" if ready else "not_ready",
            "service": config.service_name,
            "probes": [result.__dict__ for result in results],
        }
        status_code = status.HTTP_200_OK if ready else status.HTTP_503_SERVICE_UNAVAILABLE
        return JSONResponse(payload, status_code=status_code)

    @app.get(config.metrics.path)
    async def metrics():
        data = generate_latest(app.state.registry)
        return Response(content=data, media_type=CONTENT_TYPE_LATEST)

    return app


__all__ = ["create_app", "build_metrics_registry"]