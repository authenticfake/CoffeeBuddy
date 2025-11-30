# FINALIZE

## Project Overview
CoffeeBuddy is an on-prem Slack bot that orchestrates coffee runs from slash command through reminders. It runs on Python 3.12, persists state in Postgres, exchanges lifecycle events over Kafka, surfaces APIs through FastAPI behind Kong, and exposes Prometheus metrics for SRE teams. Runner assignment follows transparent fairness rules, reminders are scheduled through Kafka-driven jobs, and admin commands manage per-channel policy.

## Badges
- ![CLike](https://img.shields.io/badge/pipeline-CLike-blue.svg)
- ![Python](https://img.shields.io/badge/python-3.12%2B-blue.svg)
- ![FastAPI](https://img.shields.io/badge/framework-FastAPI-009688.svg)
- ![Docker](https://img.shields.io/badge/docker-ready-2496ED.svg)
- ![Kafka](https://img.shields.io/badge/messaging-Kafka-231F20.svg)
- ![Postgres](https://img.shields.io/badge/db-Postgres-336791.svg)

## Architecture Sketch
```
Slack slash commands → Kong → FastAPI service (coffeebuddy)
FastAPI service ↔ Postgres (runs, orders, preferences)
FastAPI service ↔ Kafka (run/reminder events) ↔ Reminder worker
Service ↔ Vault (secrets), Ory (OIDC), Prometheus (/metrics)
```

## Repository Layout
- `src/coffeebuddy/api`: FastAPI routers for Slack slash commands, interactions, and admin UX.
- `src/coffeebuddy/core`: Business logic for orders, runs, fairness, audit trails.
- `src/coffeebuddy/jobs/reminders`: Kafka-driven reminder worker and scheduler glue.
- `src/coffeebuddy/infra/db`: SQLAlchemy models, migrations, retention helpers.
- `src/coffeebuddy/infra/kafka`: Topic definitions, producer/consumer utilities, metrics hooks.
- `tests/`: Pytest suites covering handlers, fairness, reminders, admin commands, infra helpers.
- `docs/`: Functional specs, plans, and Harper outputs.

## Quickstart
### CLI
```bash
python -m venv .venv && source .venv/bin/activate
pip install -e .
export $(cat .env.example | xargs)  # or use direnv
uvicorn coffeebuddy.app:app --host 0.0.0.0 --port 8000 --reload
python -m coffeebuddy.jobs.reminders.worker
```

### Docker
```bash
docker compose build
docker compose up coffeebuddy api kafka reminder-worker
# Logs
docker compose logs -f api
# Teardown
docker compose down -v
```

## Configuration
| Variable | Required | Default | Description |
| --- | --- | --- | --- |
| `SLACK_SIGNING_SECRET` | yes | — | Verifies slash commands/interactions. |
| `SLACK_BOT_TOKEN` | yes | — | Sends channel messages, DMs. |
| `DATABASE_URL` | yes | — | Postgres DSN (Vault injected). |
| `KAFKA_BROKERS` | yes | — | Bootstrap servers for events. |
| `KAFKA_SASL_JAAS` | optional | — | SASL auth string if enabled. |
| `REMINDER_CONCURRENCY` | optional | `4` | Max in-flight reminder jobs. |
| `FAIRNESS_WINDOW_RUNS` | optional | `5` | Default fairness rolling window. |
| `REMINDER_OFFSET_MINUTES` | optional | `5` | Default runner reminder offset. |
| `PROMETHEUS_MULTIPROC_DIR` | optional | — | Enables multiprocess metrics. |

Services and Ports:
- FastAPI service exposed internally on `:8000`.
- Prometheus scrapes `:8000/metrics`.
- Health probes: `:8000/health/live`, `:8000/health/ready`.
- Kafka/ Postgres ports handled via platform defaults; see `docker-compose.yml`.

## Made with CLike
This delivery follows the Harper pipeline (SPEC → PLAN → KIT) and passes KIT gates for all REQ IDs.

## Testing & Quality
- Run unit and integration tests: `pytest -q`.
- Lint/type (if configured): `ruff check`, `mypy`.
- CI enforces ≥80% coverage (tech constraints).
- Manual sanity: start service, trigger `/coffee`, close run, verify Kafka reminder emission.

## Assumptions
- Vault injects secrets (.env is dev-only).
- Kong route already configured to forward Slack traffic.
- Kafka/Postgres locally provisioned via docker compose or corporate platform.