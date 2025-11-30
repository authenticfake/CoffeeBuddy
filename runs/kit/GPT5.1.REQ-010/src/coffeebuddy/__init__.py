"""
CoffeeBuddy package root.

This REQ-010 KIT provides the initial runtime wiring for the CoffeeBuddy
service, including the ASGI app factory, health endpoints, metrics, and
integration hooks for Vault and Ory.
"""

__all__ = ["__version__"]

__version__ = "0.1.0"

file:/runs/kit/REQ-010/src/coffeebuddy/infrastructure/__init__.py
"""
Infrastructure layer for CoffeeBuddy.

REQ-010 introduces the `runtime` module, which is responsible for
Kubernetes-facing runtime behavior: ASGI app wiring, health endpoints,
and hooks to platform services like Vault, Ory, and Prometheus.
"""

file:/runs/kit/REQ-010/src/coffeebuddy/infrastructure/runtime/__init__.py
"""
Runtime integration layer for CoffeeBuddy (REQ-010).

This package exposes:

- Settings: environment-driven configuration for runtime wiring.
- Vault and Ory client abstractions and default HTTP implementations.
- `create_app`: the FastAPI application factory with health and metrics
  endpoints suitable for Kubernetes + Kong deployment.
"""

from .app import create_app, Settings

__all__ = ["create_app", "Settings"]

file:/runs/kit/REQ-010/src/coffeebuddy/infrastructure/runtime/settings.py
from __future__ import annotations

from functools import lru_cache
from typing import Literal, Optional

from pydantic import BaseSettings, Field, AnyHttpUrl, validator


class Settings(BaseSettings):
    """
    Runtime configuration for the CoffeeBuddy service.

    All values are driven via environment variables to keep deployment
    flexible across Kubernetes environments.

    This settings model is intentionally minimal for REQ-010 and is
    expected to be extended in later REQs (DB, Kafka, etc.).
    """

    app_name: str = Field("coffeebuddy", env="COFFEEBUDDY_APP_NAME")
    environment: Literal["dev", "test", "prod"] = Field(
        "dev", env="COFFEEBUDDY_ENVIRONMENT"
    )
    # HTTP bind address information (used in manifests / runner scripts).
    http_host: str = Field("0.0.0.0", env="COFFEEBUDDY_HTTP_HOST")
    http_port: int = Field(8080, env="COFFEEBUDDY_HTTP_PORT")

    # Vault integration
    vault_addr: Optional[AnyHttpUrl] = Field(
        default=None, env="VAULT_ADDR", description="Base URL for Vault HTTP API."
    )
    vault_token: Optional[str] = Field(
        default=None,
        env="VAULT_TOKEN",
        description="Token for Vault, injected via Kubernetes secret.",
    )

    # Ory integration (e.g., for OIDC-related checks if needed)
    ory_base_url: Optional[AnyHttpUrl] = Field(
        default=None,
        env="ORY_BASE_URL",
        description="Base URL for Ory services (e.g., Keto/Hydra).",
    )

    metrics_path: str = Field(
        "/metrics",
        env="COFFEEBUDDY_METRICS_PATH",
        description="Path at which Prometheus metrics are exposed.",
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    @validator("http_port")
    def validate_port(cls, v: int) -> int:
        if not (1 <= v <= 65535):
            raise ValueError("http_port must be between 1 and 65535")
        return v


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Cached accessor for Settings used by the application factory.

    Using lru_cache ensures deterministic behavior for a given process
    and avoids repeatedly parsing environment variables.
    """
    return Settings()

file:/runs/kit/REQ-010/src/coffeebuddy/infrastructure/runtime/clients.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable, Optional

import httpx

from .settings import Settings


@runtime_checkable
class VaultClient(Protocol):
    """
    Abstraction for Vault health and secret access.

    Only a health check is required for REQ-010 readiness probing.
    Additional methods can be added in later REQs without breaking
    existing code.
    """

    async def health_check(self) -> bool:
        """
        Return True if Vault is reachable and reports a healthy state.

        Implementations MUST NOT log secrets or tokens.
        """
        ...


@runtime_checkable
class OryClient(Protocol):
    """
    Abstraction for Ory readiness.

    For REQ-010, we only use this for a basic health check. Later REQs
    may extend this with token validation helpers and auth policies.
    """

    async def health_check(self) -> bool:
        """
        Return True if the Ory control plane is reachable and healthy.
        """
        ...


@dataclass
class HttpVaultClient:
    """
    HTTP-based implementation of VaultClient using httpx.

    This client targets the standard Vault health endpoint and returns
    True when Vault reports a healthy status (2xx response codes).

    All configuration is provided via `Settings` and environment.
    """

    base_url: str
    token: Optional[str]

    async def health_check(self) -> bool:
        if not self.base_url:
            # When Vault is not configured, treat as unhealthy for
            # readiness so operators can detect misconfiguration.
            return False

        headers = {}
        if self.token:
            headers["X-Vault-Token"] = self.token

        async with httpx.AsyncClient(base_url=self.base_url, timeout=2.0) as client:
            try:
                resp = await client.get("/v1/sys/health", headers=headers)
            except httpx.HTTPError:
                return False
        # Vault typically returns 200 for healthy, 429/472/473 for
        # standby/recovery states. For pilot we treat only 2xx as fully
        # ready.
        return 200 <= resp.status_code < 300


@dataclass
class HttpOryClient:
    """
    HTTP-based implementation of OryClient using httpx.

    This client calls a generic /health/ready endpoint, which matches
    Ory's typical health API surface.
    """

    base_url: str

    async def health_check(self) -> bool:
        if not self.base_url:
            return False

        async with httpx.AsyncClient(base_url=self.base_url, timeout=2.0) as client:
            try:
                resp = await client.get("/health/ready")
            except httpx.HTTPError:
                return False
        return 200 <= resp.status_code < 300


def build_vault_client(settings: Settings) -> VaultClient:
    """
    Construct the default Vault client from settings.

    This is the production path used by `create_app` when no explicit
    client override is supplied.
    """
    return HttpVaultClient(
        base_url=str(settings.vault_addr) if settings.vault_addr else "",
        token=settings.vault_token,
    )


def build_ory_client(settings: Settings) -> OryClient:
    """
    Construct the default Ory client from settings.
    """
    return HttpOryClient(
        base_url=str(settings.ory_base_url) if settings.ory_base_url else ""
    )

file:/runs/kit/REQ-010/src/coffeebuddy/infrastructure/runtime/app.py
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

file:/runs/kit/REQ-010/src/coffeebuddy/infrastructure/runtime/k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: coffeebuddy
  labels:
    app: coffeebuddy
spec:
  replicas: 2
  selector:
    matchLabels:
      app: coffeebuddy
  template:
    metadata:
      labels:
        app: coffeebuddy
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8080"
        prometheus.io/path: "/metrics"
    spec:
      containers:
        - name: coffeebuddy
          image: coffeebuddy:latest
          imagePullPolicy: IfNotPresent
          ports:
            - containerPort: 8080
              name: http
          env:
            - name: COFFEEBUDDY_ENVIRONMENT
              value: "prod"
            - name: COFFEEBUDDY_HTTP_PORT
              value: "8080"
            - name: VAULT_ADDR
              valueFrom:
                secretKeyRef:
                  name: coffeebuddy-vault
                  key: vault_addr
            - name: VAULT_TOKEN
              valueFrom:
                secretKeyRef:
                  name: coffeebuddy-vault
                  key: vault_token
            - name: ORY_BASE_URL
              valueFrom:
                configMapKeyRef:
                  name: coffeebuddy-config
                  key: ory_base_url
          readinessProbe:
            httpGet:
              path: /health/ready
              port: http
            initialDelaySeconds: 10
            periodSeconds: 10
            timeoutSeconds: 2
            failureThreshold: 3
          livenessProbe:
            httpGet:
              path: /health/live
              port: http
            initialDelaySeconds: 10
            periodSeconds: 10
            timeoutSeconds: 2
            failureThreshold: 3

---
apiVersion: v1
kind: Service
metadata:
  name: coffeebuddy
  labels:
    app: coffeebuddy
spec:
  selector:
    app: coffeebuddy
  ports:
    - name: http
      port: 8080
      targetPort: http

file:/runs/kit/REQ-010/src/coffeebuddy/infrastructure/runtime/kong/route.yaml
apiVersion: configuration.konghq.com/v1
kind: KongIngress
metadata:
  name: coffeebuddy-slack
proxy:
  protocol: https
  path: /
route:
  methods:
    - POST
  strip_path: false
  preserve_host: true
---
apiVersion: v1
kind: Service
metadata:
  name: coffeebuddy-slack
  labels:
    app: coffeebuddy
spec:
  selector:
    app: coffeebuddy
  ports:
    - name: http
      port: 8080
      targetPort: http

file:/runs/kit/REQ-010/test/infrastructure/test_runtime_app.py
import asyncio
from typing import Any

import pytest
from httpx import AsyncClient
from httpx import ASGITransport
from prometheus_client import CollectorRegistry, Counter

from coffeebuddy.infrastructure.runtime import Settings, create_app
from coffeebuddy.infrastructure.runtime.clients import OryClient, VaultClient


class _HealthyVaultClient(VaultClient):
    async def health_check(self) -> bool:  # type: ignore[override]
        return True


class _UnhealthyVaultClient(VaultClient):
    async def health_check(self) -> bool:  # type: ignore[override]
        return False


class _HealthyOryClient(OryClient):
    async def health_check(self) -> bool:  # type: ignore[override]
        return True


class _UnhealthyOryClient(OryClient):
    async def health_check(self) -> bool:  # type: ignore[override]
        return False


@pytest.mark.asyncio
async def test_health_live_ok() -> None:
    app = create_app(
        Settings(), vault_client_factory=lambda s: _HealthyVaultClient(), ory_client_factory=lambda s: _HealthyOryClient()
    )
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        resp = await client.get("/health/live")
    assert resp.status_code == 200
    assert resp.json()["status"] == "live"


@pytest.mark.asyncio
async def test_health_ready_ok_when_all_dependencies_healthy() -> None:
    app = create_app(
        Settings(), vault_client_factory=lambda s: _HealthyVaultClient(), ory_client_factory=lambda s: _HealthyOryClient()
    )

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        resp = await client.get("/health/ready")

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["status"] == "ready"
    assert payload["components"]["vault"] == "ok"
    assert payload["components"]["ory"] == "ok"


@pytest.mark.asyncio
async def test_health_ready_503_when_vault_unhealthy() -> None:
    app = create_app(
        Settings(),
        vault_client_factory=lambda s: _UnhealthyVaultClient(),
        ory_client_factory=lambda s: _HealthyOryClient(),
    )

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        resp = await client.get("/health/ready")

    assert resp.status_code == 503
    payload = resp.json()
    assert payload["detail"]["status"] == "degraded"
    assert payload["detail"]["components"]["vault"] == "unavailable"
    assert payload["detail"]["components"]["ory"] == "ok"


@pytest.mark.asyncio
async def test_health_ready_503_when_ory_unhealthy() -> None:
    app = create_app(
        Settings(),
        vault_client_factory=lambda s: _HealthyVaultClient(),
        ory_client_factory=lambda s: _UnhealthyOryClient(),
    )

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        resp = await client.get("/health/ready")

    assert resp.status_code == 503
    payload = resp.json()
    assert payload["detail"]["status"] == "degraded"
    assert payload["detail"]["components"]["vault"] == "ok"
    assert payload["detail"]["components"]["ory"] == "unavailable"


@pytest.mark.asyncio
async def test_metrics_endpoint_uses_registry_and_returns_prometheus_format() -> None:
    registry = CollectorRegistry()
    # Create a simple counter so that the output is non-empty and deterministic.
    c = Counter("coffeebuddy_test_counter_total", "Test counter", registry=registry)
    c.inc()

    app = create_app(
        Settings(), vault_client_factory=lambda s: _HealthyVaultClient(), ory_client_factory=lambda s: _HealthyOryClient(), registry=registry
    )

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        resp = await client.get("/metrics")

    assert resp.status_code == 200
    assert "coffeebuddy_test_counter_total" in resp.text

file:/runs/kit/REQ-010/docs/KIT_REQ-010.md
# KIT — REQ-010 Runtime integration with Kubernetes, Kong, Vault, Ory, Prometheus

## Scope

This KIT delivers the initial runtime wiring for CoffeeBuddy:

- ASGI application factory (`create_app`) using FastAPI.
- Health endpoints for Kubernetes:
  - `/health/live`
  - `/health/ready`
- Prometheus metrics endpoint at a configurable path (default `/metrics`).
- Abstractions and default HTTP clients for:
  - Vault health checks.
  - Ory health checks.
- Example Kubernetes `Deployment` and `Service` manifests with probes and
  Prometheus annotations.
- Example Kong route configuration to expose the service to Slack via
  Kong Gateway.

## Design Overview

### Modules

- `coffeebuddy.infrastructure.runtime.settings`
  - `Settings` (`pydantic.BaseSettings`): environment-driven configuration.
  - `get_settings()`: cached accessor used in `create_app`.

- `coffeebuddy.infrastructure.runtime.clients`
  - `VaultClient` / `OryClient` protocols for dependency inversion.
  - `HttpVaultClient` / `HttpOryClient` production implementations using
    `httpx.AsyncClient`.
  - `build_vault_client(settings)` / `build_ory_client(settings)` factory
    helpers for application wiring.

- `coffeebuddy.infrastructure.runtime.app`
  - `create_app(settings, vault_client_factory, ory_client_factory, registry)`:
    builds the FastAPI app, wires dependencies, and registers routes:
    - `/health/live`
    - `/health/ready`
    - `/metrics` (path configurable via `Settings.metrics_path`)

### Health Behavior

- `/health/live`
  - Cheap, synchronous liveness check.
  - No external calls; just returns `{"status": "live"}`.

- `/health/ready`
  - Async readiness probe that calls:
    - `VaultClient.health_check()`
    - `OryClient.health_check()`
  - Returns:
    - `200` with `{"status": "ready", "components": {...}}` if both OK.
    - `503` with `{"status": "degraded", "components": {...}}` in
      `detail` when any dependency is unavailable.
  - This aligns with Kubernetes readiness semantics and acceptance
    criteria requiring Vault/Ory wiring.

### Metrics

- `/metrics`
  - Exposes Prometheus metrics in text format using `prometheus_client`.
  - When `registry` is passed into `create_app`, it is used; otherwise,
    the global default registry is used.
  - K8s manifests include Prometheus scrape annotations.

### Kubernetes & Kong

- `k8s/deployment.yaml`
  - `Deployment` with:
    - Probes configured for `/health/live` and `/health/ready`.
    - Environment variables for Vault and Ory configuration.
    - Prometheus annotations for metrics scraping.
  - `Service` exposing port `8080`.

- `kong/route.yaml`
  - Example KongIngress and Service configuration to expose
    CoffeeBuddy to Slack via Kong Gateway over HTTPS.

## Testing

Unit tests live under `runs/kit/REQ-010/test/infrastructure` and cover:

- Liveness endpoint returns 200 and `"live"`.
- Readiness endpoint:
  - Returns 200 when Vault and Ory are healthy (via injected fake
    clients).
  - Returns 503 and clear component status when any dependency is
    unhealthy.
- Metrics endpoint:
  - Uses the provided `CollectorRegistry`.
  - Returns valid Prometheus text that includes a test counter.

Tests use `httpx.AsyncClient` with `ASGITransport` to exercise the FastAPI
application in-process without external network calls.

## Extensibility Notes

- Additional platform integrations (Postgres, Kafka, Slack) should be
  wired via new client protocols and injected into `create_app` or
  separate application composition modules.
- Observability (correlation IDs, structured logging) will be extended
  in REQ-007 but the current design keeps a clear seam via the app
  factory and dependency injection.

file:/runs/kit/REQ-010/docs/README_REQ-010.md
# REQ-010 — Runtime integration with Kubernetes, Kong, Vault, Ory, Prometheus

This REQ establishes the CoffeeBuddy runtime shell that can be deployed
to Kubernetes and integrated with the on-prem platform stack.

## What’s included

- FastAPI-based ASGI application factory:
  - `coffeebuddy.infrastructure.runtime.create_app`
- Health endpoints:
  - `GET /health/live` — liveness.
  - `GET /health/ready` — readiness (Vault + Ory health).
- Prometheus metrics endpoint:
  - `GET /metrics` (path configurable via `COFFEEBUDDY_METRICS_PATH`).
- Vault and Ory HTTP clients behind small Protocol interfaces.
- Example Kubernetes Deployment/Service with probes and Prometheus
  annotations.
- Example Kong route configuration for Slack-facing traffic.
- Unit tests for health and metrics behavior.

## Configuration

Configuration is environment-driven via `Settings` (`pydantic.BaseSettings`):

- `COFFEEBUDDY_APP_NAME` (default `coffeebuddy`)
- `COFFEEBUDDY_ENVIRONMENT` (`dev` | `test` | `prod`, default `dev`)
- `COFFEEBUDDY_HTTP_HOST` (default `0.0.0.0`)
- `COFFEEBUDDY_HTTP_PORT` (default `8080`)
- `VAULT_ADDR` — base URL for Vault (e.g. `https://vault.internal:8200`)
- `VAULT_TOKEN` — Vault token (from Kubernetes Secret)
- `ORY_BASE_URL` — base URL for Ory services
- `COFFEEBUDDY_METRICS_PATH` — metrics path (default `/metrics`)

## How to run locally

From the project root: