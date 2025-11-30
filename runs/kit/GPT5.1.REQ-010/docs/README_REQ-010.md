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

```bash
python -m venv .venv
source .venv/bin/activate

pip install -r runs/kit/REQ-010/requirements.txt

export COFFEEBUDDY_ENVIRONMENT=dev
export COFFEEBUDDY_HTTP_PORT=8080

uvicorn coffeebuddy.infrastructure.runtime.app:create_app --factory --host 0.0.0.0 --port 8080
```

Then visit:

- `http://localhost:8080/health/live`
- `http://localhost:8080/health/ready`
- `http://localhost:8080/metrics`

## How to run tests

```bash
python -m venv .venv
source .venv/bin/activate

pip install -r runs/kit/REQ-010/requirements.txt

pytest -q runs/kit/REQ-010/test
```

## Notes and Assumptions

- Vault and Ory are treated as required for readiness. When they are
  misconfigured or unavailable, `/health/ready` returns `503` so
  Kubernetes can avoid routing traffic to the pod.
- Secrets (Vault token, etc.) must be provided via Kubernetes Secrets
  and MUST NOT be logged. This KIT only surfaces their presence via
  configuration; logging and tracing details will be addressed in
  REQ-007.