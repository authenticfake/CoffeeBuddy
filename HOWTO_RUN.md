## HOWTO_RUN

### CLI Services
- **API service**
  - `poetry run alembic upgrade head`
  - `poetry run uvicorn coffeebuddy.api.main:app --host 0.0.0.0 --port "${SERVICE_PORT}"`
- **Reminder worker / scheduler**
  - `poetry run python -m coffeebuddy.jobs.reminders.consumer`
  - Optional periodic scheduler: `poetry run python -m coffeebuddy.jobs.reminders.scheduler`
- **Admin/audit maintenance**
  - Use `/coffee admin` from Slack once API is reachable; no separate CLI.

### API / Postman
- Export latest OpenAPI (FastAPI auto-docs) and convert to Postman:
  - `curl http://localhost:${SERVICE_PORT}/openapi.json -o artifacts/coffeebuddy-openapi.json`
  - Import JSON into Postman and save as `docs/postman/CoffeeBuddy.postman_collection.json`.
- Core endpoints:
  - Slack ingress: `/slack/events` (slash + interactions routed through Kong).
  - Health: `/health/live`, `/health/ready`.
  - Metrics: `/metrics`.
- Use collection to simulate slash/interaction payloads (set `X-Slack-Signature`/`X-Slack-Request-Timestamp` headers).

### Docker / Compose
- Build images: `docker build -t coffeebuddy:latest .`
- Bring up stack (API, worker, Postgres, Kafka, zookeeper):
  - `docker compose up --build api worker db kafka`
- Verify configuration: `docker compose config`
- Health checks:
  - `curl -f http://localhost:${SERVICE_PORT}/health/ready`
  - `docker compose logs api | tail -n 50`
- Teardown & cleanup: `docker compose down -v`

### Broker (Kafka)
- Topics (from `coffeebuddy.infra.kafka`):
  - `coffeebuddy.run.events`
  - `coffeebuddy.reminder.events`
- Local broker via compose profile `kafka`; remote broker via platform-managed cluster (set `KAFKA_BOOTSTRAP_SERVERS`).
- Reminder consumer group: `coffeebuddy-reminders`.
- Use `kafkacat -b ${KAFKA_BOOTSTRAP_SERVERS} -t coffeebuddy.run.events -C` to inspect payloads.

### Environment Variables
| Variable | Type | Notes |
| --- | --- | --- |
| `SERVICE_PORT` | Required | Propagated to uvicorn and Kong upstream configuration. |
| `SLACK_SIGNING_SECRET` | Required | Must match Slack app config; loaded from Vault at startup. |
| `SLACK_BOT_TOKEN` | Required | Enables posting channel messages/DMs. |
| `DATABASE_URL` | Required | Postgres DSN; `postgresql+psycopg` recommended. |
| `ALEMBIC_CONFIG` | Optional | Override path for migrations (default `alembic.ini`). |
| `KAFKA_BOOTSTRAP_SERVERS` | Required | Broker list for producer/consumer clients. |
| `KAFKA_RUN_TOPIC` | Optional | Overrides default `coffeebuddy.run.events`. |
| `KAFKA_REMINDER_TOPIC` | Optional | Overrides default `coffeebuddy.reminder.events`. |
| `ORY_ISSUER_URL` | Required | OIDC issuer for service-to-service auth. |
| `ORY_AUDIENCE` | Optional | Custom audience if platform mandates. |
| `VAULT_ADDR` | Required | Vault endpoint. |
| `VAULT_ROLE` | Required | Role/AppRole used to fetch secrets. |
| `.env` handling | – | Load via `python-dotenv` if present; otherwise rely on platform secret injection. |

### Assumptions
- Kong routes `/slack/events` and `/slack/interactions` to `${SERVICE_PORT}` with TLS termination upstream.
- Vault sidecar or init container injects `SLACK_*`, `DATABASE_URL`, and Kafka credentials prior to container start.