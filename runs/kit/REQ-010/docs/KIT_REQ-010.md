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