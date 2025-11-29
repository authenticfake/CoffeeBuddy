# CoffeeBuddy

![Python](https://img.shields.io/badge/python-3.12-blue.svg) ![FastAPI](https://img.shields.io/badge/FastAPI-ready-green.svg) ![Docker](https://img.shields.io/badge/docker-compose-blue.svg) ![Kubernetes](https://img.shields.io/badge/k8s-ready-326ce5.svg) ![CLike](https://img.shields.io/badge/built_with-CLike-black.svg)

## Overview
CoffeeBuddy is an on-prem Slack bot that streamlines office coffee runs: start a run with `/coffee`, capture orders (including “reuse my usual”), assign a fair runner, and send summaries plus reminders. The service is a FastAPI app running on Kubernetes, backed by Postgres for state, Kafka for events/reminders, Vault for secrets, and exposed via Kong.

## Architecture
```
Slack → Kong → CoffeeBuddy (FastAPI + Slack SDK)
  ├─ Postgres (runs, orders, preferences, configs)
  ├─ Kafka (run + reminder topics)
  ├─ Vault (Slack tokens, DB creds)
  ├─ Ory (OIDC auth to internal services)
  └─ Prometheus scrape (/metrics)
```
Slices:
- `coffeebuddy.api.slack_runs`: slash commands, interactive payloads.
- `coffeebuddy.core.orders/runs`: persistence + fairness logic.
- `coffeebuddy.jobs.reminders`: Kafka reminder worker.
- `coffeebuddy.api.admin`: channel enable/disable, config, data reset.
- `coffeebuddy.infra.db/kafka`: schema, migrations, topic definitions.

## Repository Layout
- `src/coffeebuddy/api/`: FastAPI routers for Slack and admin flows.
- `src/coffeebuddy/core/`: business services (orders, runs, fairness, audit).
- `src/coffeebuddy/jobs/`: Kafka reminder consumer & scheduler.
- `src/coffeebuddy/infra/`: DB session factory, schema loader, Kafka utilities.
- `src/storage/spec/` + `src/storage/sql/`: canonical schema + Alembic migrations.
- `tests/`: pytest suites per REQ (unit + integration).
- `docker/` + `compose.yaml`: local runtime wiring (app, Postgres, Kafka).
- `docs/`: Harper runbooks and API collections.

## Quickstart

### CLI (dev)
```bash
python -m venv .venv && source .venv/bin/activate
pip install -e .[dev]
export SLACK_SIGNING_SECRET=...
export SLACK_BOT_TOKEN=...
export DATABASE_URL=postgresql+psycopg://...
export KAFKA_BOOTSTRAP=localhost:9092
alembic upgrade head
uvicorn coffeebuddy.main:app --host 0.0.0.0 --port 8080 --reload
```

### Docker
```bash
docker compose up --build
# App: http://localhost:8080 (Kong mock in front if configured)
# Check health:
curl -f http://localhost:8080/health/ready
```
Teardown with `docker compose down -v`.

## Configuration
| Variable | Required | Default | Description |
| --- | --- | --- | --- |
| `SLACK_SIGNING_SECRET` | ✅ | — | Verifies Slack payloads. Loaded from Vault in prod. |
| `SLACK_BOT_TOKEN` | ✅ | — | Bot token for posting messages/DMs. |
| `DATABASE_URL` | ✅ | — | SQLAlchemy DSN for Postgres. |
| `KAFKA_BOOTSTRAP` | ✅ | — | Kafka bootstrap servers. |
| `KAFKA_SASL_JAAS` | ⚪️ | None | SASL config when using secured clusters. |
| `VAULT_ADDR` / `VAULT_TOKEN` | ⚪️ | platform | Secret retrieval when not using sidecars. |
| `PROMETHEUS_MULTIPROC_DIR` | ⚪️ | None | Enables multiprocess metrics if Gunicorn. |
| `RUN_FAIRNESS_WINDOW` | ⚪️ | 5 | Fallback channel fairness window if not configured. |
| `REMINDER_OFFSET_DEFAULT` | ⚪️ | 5 | Fallback reminder minutes before pickup. |
| `DISABLE_REMINDERS` | ⚪️ | false | Global kill switch for reminder worker. |

Services & Ports (dev defaults):
- FastAPI app: `:8080`
- Postgres (compose): `:5432`
- Kafka (compose): `:9092`

## Quick Ops
- Health: `/health/live`, `/health/ready`
- Metrics: `/metrics` (Prometheus format)
- Slack ingress: `/slack/commands`, `/slack/interactions` via Kong route
- Reminder worker entrypoint: `python -m coffeebuddy.jobs.reminders.worker`

## Testing & Quality
- Unit/integration: `pytest -q`
- Style: `ruff check .`
- Types: `mypy src`
- Coverage target: ≥80% per TECH_CONSTRAINTS.
- CI ensures migrations idempotent and Kafka topic configs render.

## Acceptance Criteria
- Slash commands acknowledge within 2 s and persist runs with correlation IDs.
- Orders modal enforces validation, updates participant counts, and preserves preferences.
- Closing a run assigns runner per fairness rules, posts channel summary, and DMs runner.
- Reminder jobs trigger at `pickup_time - offset` ±1 minute unless disabled.
- Admin disable/reset commands block new runs and purge historical data for the channel.

## Made With
Built with CLike Harper pipeline (IDEA→SPEC→PLAN→KIT), FastAPI, SQLAlchemy, Kafka Python clients, and pytest. See `SPEC.md`/`PLAN.md` for traceability.

## Assumptions
- Slack app configured with required scopes and channel installation.
- Kong/Ory/Vault endpoints reachable inside target cluster.
- Time sync (NTP) within 1 minute to honor reminder tolerances.