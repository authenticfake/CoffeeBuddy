# FINALIZE

## CLI Workflow
- **API Service**
  ```bash
  source .venv/bin/activate  # ensure dependencies installed
  uvicorn coffeebuddy.main:app --host 0.0.0.0 --port 8080 --reload
  ```
  - Health checks: `curl http://localhost:8080/health/live` and `/health/ready`.
  - Metrics: `curl http://localhost:8080/metrics`.
- **Reminder Worker**
  ```bash
  export KAFKA_CONSUMER_GROUP=coffeebuddy-reminders-dev
  python -m coffeebuddy.jobs.reminders.consumer
  ```
  The worker consumes `coffeebuddy.reminder.events` and posts Slack DMs via shared Slack client helpers.
- **Scheduler Trigger (optional)**
  ```bash
  python -m coffeebuddy.jobs.reminders.scheduler --dry-run
  ```
  Use to backfill reminder jobs if Kafka downtime occurs.

## API & Postman
- FastAPI docs (if enabled) at `http://localhost:8080/docs` for internal operations endpoints (`/health`, `/metrics`).
- Slack-facing routes are POST endpoints under `/slack/commands` and `/slack/interactions`.
- Postman collection: `docs/postman/coffeebuddy.postman_collection.json`.
  - Import, set environment variables (`slackSigningSecret`, `apiBaseUrl`, `botToken`).
  - Collection includes flows for `/coffee`, order modal submissions, admin commands, and reminder callbacks.

## Docker & Compose
```bash
docker compose -f deploy/docker-compose.yml up --build
# Follow logs
docker compose logs -f api worker kafka
# Health verification
docker compose exec api curl -f http://localhost:8080/health/ready
# Shutdown
docker compose -f deploy/docker-compose.yml down -v
```
- **Health Checks**: Kubernetes probes map to `/health/live` and `/health/ready`. Compose exposes the same endpoints.
- **Logs**: Structured JSON logs stream via `docker compose logs -f`.
- **Teardown**: Always include `-v` to drop local Postgres volumes when refreshing schema.

## Broker Details
- Local development spins up a single-node Kafka via Compose; production references platform-managed brokers.
- Topics:
  - `coffeebuddy.run.events`: produced by API, consumed by analytics/reminder scheduler.
  - `coffeebuddy.reminder.events`: produced by scheduler, consumed by reminder worker.
- ACL expectations: service principal `svc_coffeebuddy` requires `WRITE` on run events and `READ` on reminder events.

## Env Vars & .env Strategy
| Variable | Scope | Notes |
| --- | --- | --- |
| `SLACK_BOT_TOKEN` | API & worker | Vault-injected in prod; load from `.env` for local testing. |
| `SLACK_SIGNING_SECRET` | API | Required to verify Slack signatures. |
| `DATABASE_URL` | API | Points to Postgres; Compose wires `postgres://cbuddy:cbuddy@postgres:5432/coffeebuddy`. |
| `KAFKA_BOOTSTRAP_SERVERS` | API & worker | Example: `kafka:9092` in Compose. |
| `KAFKA_SASL_*` | Worker (optional) | Enable when brokers require SASL/SCRAM. |
| `ORY_ISSUER` | API | Needed when calling other cluster services. |
| `REMINDER_OFFSET_DEFAULT` | API | Seed value overridden per channel. |
| `.env` loading | CLI | `python-dotenv` auto-loads `.env` when present; keep secrets out of VCS. For Compose, reference `deploy/.env.example` and copy to `.env`. |

## Assumptions
- `deploy/docker-compose.yml` provisions Postgres, Kafka, and optional Kong mock.
- Postman collection exists at the documented path; regenerate if missing via internal tooling.