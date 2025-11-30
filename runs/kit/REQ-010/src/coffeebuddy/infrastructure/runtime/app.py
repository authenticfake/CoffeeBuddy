from __future__ import annotations

from typing import Callable, Optional

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import JSONResponse, Response
from starlette.requests import Request

from prometheus_client import CONTENT_TYPE_LATEST, CollectorRegistry, generate_latest

from .clients import OryClient, VaultClient, build_ory_client, build_vault_client
from .settings import Settings, get_settings


def _get_vault_client(request: Request) -> VaultClient:
    return request.app.state.vault_client  # type: ignore[no-any-return]


def _get_ory_client(request: Request) -> OryClient:
    return request.app.state.ory_client  # type: ignore[no-any-return]


def create_app(
    settings: Optional[Settings] = None,
    *,
    vault_client_factory: Optional[Callable[[Settings], VaultClient]] = None,
    ory_client_factory: Optional[Callable[[Settings], OryClient]] = None,
    registry: Optional[CollectorRegistry] = None,
) -> FastAPI:
    """
    Application factory for the CoffeeBuddy service.

    - Provides `/health/live` and `/health/ready` for Kubernetes probes.
    - Exposes `/metrics` in Prometheus format.
    - Wires Vault and Ory health checks via injected client factories.

    Parameters
    ----------
    settings:
        Optional explicit Settings instance; when None, environment-driven
        `get_settings()` is used (cached).
    vault_client_factory:
        Factory to create the VaultClient. Used to inject fakes in tests.
    ory_client_factory:
        Factory to create the OryClient. Used to inject fakes in tests.
    registry:
        Optional Prometheus CollectorRegistry. If None, the default
        global registry is used.
    """
    cfg = settings or get_settings()

    app = FastAPI(
        title="CoffeeBuddy",
        version="0.1.0",
        description="CoffeeBuddy runtime service (REQ-010) with health and metrics.",
    )

    # Build platform clients
    vault_factory = vault_client_factory or build_vault_client
    ory_factory = ory_client_factory or build_ory_client

    app.state.settings = cfg
    app.state.vault_client = vault_factory(cfg)
    app.state.ory_client = ory_factory(cfg)
    app.state.metrics_registry = registry

    @app.get("/health/live", tags=["health"])
    async def health_live() -> dict:
        """
        Liveness probe: indicates the process and main loop are running.

        This endpoint MUST NOT perform heavy checks or external calls.
        """
        return {"status": "live"}

    @app.get("/health/ready", tags=["health"])
    async def health_ready(
        vault: VaultClient = Depends(_get_vault_client),
        ory: OryClient = Depends(_get_ory_client),
    ) -> JSONResponse:
        """
        Readiness probe: verifies core dependencies required for serving
        traffic are available (Vault and Ory for REQ-010).

        Returns:
            200 with component statuses when ready.
            503 when any dependency is unavailable.
        """
        vault_ok = await vault.health_check()
        ory_ok = await ory.health_check()

        status = {
            "status": "ready" if (vault_ok and ory_ok) else "degraded",
            "components": {
                "vault": "ok" if vault_ok else "unavailable",
                "ory": "ok" if ory_ok else "unavailable",
            },
        }

        if not (vault_ok and ory_ok):
            # For Kubernetes, a non-2xx status on readiness is sufficient
            # to mark the pod as not ready for traffic.
            raise HTTPException(status_code=503, detail=status)

        return JSONResponse(content=status)

    @app.get(cfg.metrics_path, tags=["metrics"])
    async def metrics() -> Response:
        """
        Prometheus metrics endpoint.

        Uses either the provided `registry` (primarily for tests) or the
        default global registry created by prometheus_client.
        """
        current_registry = app.state.metrics_registry
        data = generate_latest(current_registry) if current_registry else generate_latest()
        return Response(content=data, media_type=CONTENT_TYPE_LATEST)

    return app