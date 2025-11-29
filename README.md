# FINALIZE

![Python](https://img.shields.io/badge/python-3.12-blue.svg) ![Docker](https://img.shields.io/badge/docker-ready-informational.svg) ![CLike](https://img.shields.io/badge/built%20with-CLike-8A2BE2.svg)

## Overview
CoffeeBuddy is an on-prem Slack bot that coordinates office coffee runs end-to-end: a slash command opens a run, users place or reuse orders, a fairness-aware runner is assigned, reminders fire via Kafka, and admins can govern channels. The service targets Kubernetes with Postgres, Kafka, Kong, Vault, Ory, and Prometheus integrations.

## Architecture
- Slack requests enter through Kong and terminate at the FastAPI-based CoffeeBuddy service (`coffeebuddy.api`).
- Persistence is handled via SQLAlchemy models backed by Postgres using the canonical schema in `src/storage/spec/schema.yaml`.
- Kafka topics defined in `coffeebuddy.infra.kafka` decouple run lifecycle events and reminder scheduling.
- Vault delivers Slack, Postgres, and Kafka credentials at runtime; Ory provides OIDC service auth.
- Prometheus scrapes `/metrics`, while readiness/liveness endpoints gate Kubernetes probes.

## Repository Layout
- `src/coffeebuddy/api/` – FastAPI routers for Slack slash commands, interactions, and admin flows.
- `src/coffeebuddy/core/` – Run lifecycle, order management, fairness logic, and audit utilities.
- `src/coffeebuddy/jobs/reminders/` – Kafka consumer/worker for reminder delivery.
- `src/coffeebuddy/infra/` – Database session factory, schema spec loader, Kafka topic configs.
- `tests/` – Pytest suites per REQ slice plus shared fixtures.
- `deploy/` – Helm/Compose manifests (Kubernetes deployment, docker-compose for local).
- `docs/` – SPEC, PLAN, ops guides, Harper deliverables (this file set).

## Quickstart
### CLI
```bash
# Install dependencies (adjust if Poetry/Pipenv is configured differently)
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Run FastAPI service (port 8080 by default)
uvicorn coffeebuddy.main:app --host 0.0.0.0 --port 8080

# Start reminder worker
python -m coffeebuddy.jobs.reminders.consumer
```

### Docker
```bash
# Build and start API + Postgres + Kafka stubs
docker compose -f deploy/docker-compose.yml up --build

# Check health and logs
curl http://localhost:8080/health/ready
docker compose logs -f api

# Teardown
docker compose -f deploy/docker-compose.yml down -v
```

## Configuration
| Variable | Required | Default | Description |
| --- | --- | --- | --- |
| `SLACK_BOT_TOKEN` | Yes | — | Bot token used to post channel messages and DMs. |
| `SLACK_SIGNING_SECRET` | Yes | — | Secret for verifying Slack requests via Kong ingress. |
| `DATABASE_URL` | Yes | — | Postgres DSN sourced from Vault. |
| `KAFKA_BOOTSTRAP_SERVERS` | Yes | — | Comma-separated brokers for run/reminder topics. |
| `KAFKA_SASL_USERNAME`/`KAFKA_SASL_PASSWORD` | Optional | — | Provided when cluster enforces SASL. |
| `ORY_ISSUER` | Optional | — | OIDC issuer URL for service-to-service auth. |
| `VAULT_ADDR` / `VAULT_TOKEN` | Optional | — | Override auto-injected Vault settings if running locally. |
| `PROMETHEUS_MULTIPROC_DIR` | Optional | `/tmp/coffeebuddy-prom` | Enables multiprocess metrics when using Gunicorn/Uvicorn workers. |
| `LOG_LEVEL` | Optional | `INFO` | Structured log verbosity. |
| `REMINDER_OFFSET_DEFAULT` | Optional | `5` | Minutes before pickup for reminders when channel config absent. |

## Services & Ports
| Service | Description | Port |
| --- | --- | --- |
| CoffeeBuddy API | FastAPI app serving Slack webhooks, admin UI, health, metrics | 8080 |
| Postgres (local dev) | Persistence for runs/orders/preferences | 5432 |
| Kafka (local dev) | Run events & reminder scheduling | 9092 |
| Prometheus scrape | Metrics endpoint exposed via ServiceMonitor | 8080 (`/metrics`) |

## Made with CLike
The Harper CLike pipeline produced SPEC → PLAN → KIT artifacts and this release package; see `SPEC.md` and `PLAN.md` for authoritative scope.

## Testing & Quality
- Unit/integration tests run via `pytest -q`.
- Linting via `ruff check .` (if configured in `pyproject.toml`).
- Type checks via `mypy src` when enabled.
- CI enforces ≥80% coverage per `TECH_CONSTRAINTS.yaml`.

## Acceptance Criteria
- Slash command `/coffee` validates Slack signatures, records a run with metadata, and returns an interactive message in ≤2 seconds.
- Order submissions (new or reuse) update participant counts, persist preferences, and block duplicate active orders per user/run.
- Closing a run assigns a runner per fairness rules, persists status `closed`, posts channel summary, and DM’s the runner.
- Pickup-time runs enqueue reminder jobs; runner DMs fire at `pickup_time - offset` within ±1 minute unless reminders are disabled.
- Admin `/coffee admin` enforces roles, toggles enablement, updates config bounds, and purges channel history on reset.

## Assumptions
- FastAPI entrypoint is `coffeebuddy.main:app` and listens on port 8080.
- `deploy/docker-compose.yml` exists for local orchestration; adjust commands if using Helm charts instead.
- Postman collection lives under `docs/postman/coffeebuddy.postman_collection.json`; regenerate via internal tooling if absent.