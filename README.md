# FINALIZE

![Python](https://img.shields.io/badge/python-3.12-blue.svg) ![Docker](https://img.shields.io/badge/docker-ready-0db7ed.svg) ![CLike](https://img.shields.io/badge/built%20with-CLike-8A2BE2)

## Overview
CoffeeBuddy is an on-prem Slack bot that orchestrates office coffee runs—from `/coffee` kick-off through order collection, fair runner assignment, reminders, and post-run summaries—while integrating with Postgres, Kafka, Kong, Ory, Vault, and Prometheus inside the corporate Kubernetes cluster. Made with CLike.

## Architecture Sketch
- Slack → Kong Gateway → CoffeeBuddy API (FastAPI) for slash commands and interactive payloads.
- CoffeeBuddy service persists runs, orders, preferences, configs, and audits in Postgres via `coffeebuddy.infra.db`.
- Kafka topics (`coffeebuddy.run.events`, `coffeebuddy.reminder.events`) feed reminder workers under `coffeebuddy.jobs.reminders`.
- Admin flows (`/coffee admin`) enforce authorization and log `ChannelAdminAction` rows plus metrics.
- Observability: Prometheus scrapes `/metrics`; liveness/readiness endpoints guard Kubernetes probes; structured logs embed correlation IDs.

## Repository Layout
- `src/coffeebuddy/api/`: Slack command handlers, admin surfaces, DM helpers.
- `src/coffeebuddy/core/`: Order lifecycle, run management, fairness logic, audit utilities.
- `src/coffeebuddy/jobs/`: Kafka reminder workers, schedulers, retry/backoff helpers.
- `src/coffeebuddy/infra/`: DB session factory, Alembic migrations, Kafka clients, schema spec.
- `docs/harper/`: Operational guides (this README, HOWTO, release notes, sanity checks, TODO, PR template).
- `tests/`: Pytest suites per REQ slice plus integration fixtures.

## Quickstart
### CLI
- Install deps: `poetry install` (or `pip install -r requirements.txt`).
- Apply migrations: `poetry run alembic upgrade head`.
- Launch API: `poetry run uvicorn coffeebuddy.api.main:app --host 0.0.0.0 --port "${SERVICE_PORT}"`.
- Start reminder worker: `poetry run python -m coffeebuddy.jobs.reminders.consumer`.

### Docker
- Build: `docker build -t coffeebuddy:latest .`
- Compose (API + worker + Postgres + Kafka): `docker compose up --build`
- Tear down: `docker compose down -v`
- Health check: `curl -f http://localhost:${SERVICE_PORT}/health/ready`

## Configuration
| Variable | Required | Default | Description |
| --- | --- | --- | --- |
| `SERVICE_PORT` | Yes | – | HTTP listening port forwarded by Kong. |
| `SLACK_SIGNING_SECRET` | Yes | – | Verifies slash command authenticity. |
| `SLACK_BOT_TOKEN` | Yes | – | Bot OAuth token for posting messages/DMs. |
| `DATABASE_URL` | Yes | – | Postgres connection string (Vault-injected). |
| `KAFKA_BOOTSTRAP_SERVERS` | Yes | – | Comma-separated brokers for Kafka clients. |
| `KAFKA_RUN_TOPIC` | No | `coffeebuddy.run.events` | Topic for run lifecycle events. |
| `KAFKA_REMINDER_TOPIC` | No | `coffeebuddy.reminder.events` | Topic for reminder payloads. |
| `REMINDER_OFFSET_MINUTES` | No | `5` | Default runner reminder offset. |
| `ORY_ISSUER_URL` | Yes | – | OIDC issuer for service auth. |
| `VAULT_ADDR` | Yes | – | Vault endpoint for secrets retrieval. |
| `VAULT_ROLE` | Yes | – | Vault AppRole / JWT role used to fetch secrets. |

### Services & Ports
| Service | Port/Path | Notes |
| --- | --- | --- |
| CoffeeBuddy API | `${SERVICE_PORT}` | Slash command + interaction ingress behind Kong. |
| Health probes | `/health/live`, `/health/ready` | Kubernetes liveness/readiness. |
| Metrics | `/metrics` | Prometheus scrape endpoint. |
| Kafka Brokers | platform managed | Used by `coffeebuddy.infra.kafka`. |
| Postgres | platform managed | Schema defined in `storage/spec/schema.yaml`. |

## Acceptance Criteria
- `/coffee` acknowledgements (with optional pickup metadata) render interactive controls within 2 seconds and persist an `open` run plus Kafka `run_created`.
- Order modal submissions and “Use last order” buttons update participant counts while preventing duplicate active orders per user/run.
- “Close run” enforces permissions, applies fairness (min `runs_served_count`, oldest `last_run_at`, no repeat unless opt-in), and posts identical summaries to channel + runner DM.
- Runs with pickup times enqueue reminder events; runners receive DMs at `pickup_time - reminder_offset` (±1 minute) unless reminders disabled for the channel.
- `/coffee admin` restricts actions to authorized users, persists channel config/audit entries, blocks new runs when disabled, and data resets purge run/order/preference/runner stats for that channel.

## Testing & Quality
- Run unit/integration tests: `poetry run pytest -q`.
- Lint (if configured): `poetry run ruff check src`.
- Type check (if configured): `poetry run mypy src`.
- Coverage target ≥80% per TECH_CONSTRAINTS.
- Metrics verification: `curl http://localhost:${SERVICE_PORT}/metrics`.
- Kafka/DB integration tests rely on docker compose profiles `infra-db` and `infra-kafka`.

## Assumptions
- Slack workspace, Vault mounts, Postgres, Kafka, Kong, and Ory are provisioned by platform teams.
- Postman collection is generated from OpenAPI via `poetry run python tools/export_postman.py` (see HOWTO for instructions).