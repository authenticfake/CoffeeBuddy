from __future__ import annotations

from fastapi import FastAPI

from .app import build_metrics_registry, create_app
from .config import load_service_config
from .probes import EnvironmentProbe, ReadinessRegistry


def build_runtime() -> FastAPI:
    config = load_service_config()
    readiness = ReadinessRegistry()
    readiness.register(EnvironmentProbe(config))
    registry = build_metrics_registry(config)
    return create_app(config=config, readiness_registry=readiness, registry=registry)


app = build_runtime()

__all__ = ["build_runtime", "app"]