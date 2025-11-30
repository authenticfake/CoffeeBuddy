## HOWTO_RUN

### CLI Services
1. **API service**
   ```bash
   export $(grep -v '^#' .env.local | xargs)  # optional helper
   poetry run uvicorn coffeebuddy.api.main:app --host 0.0.0.0 --port ${PORT:-8080}
   ```
   Health probes: `GET /health/live`, `GET /health/ready`. Metrics: `GET /metrics`.

2. **Reminder worker**
   ```bash
   poetry run python -m coffeebuddy.jobs.reminders.consumer \
     --group ${REMINDER_WORKER_GROUP:-coffeebuddy-reminders} \
     --topic coffeebuddy.reminder.events
   ```

3. **Scheduler/backfill (optional)**
   ```bash
   poetry run python -m coffeebuddy.jobs.reminders.backfill --dry-run
   ```

### API & Postman
- Import the Postman collection at `docs/postman/coffeebuddy.postman_collection.json` (assumption: kept in sync with FastAPI routes).
- Collection folders:
  - `Slack /coffee`: simulates slash command payloads (set `channel_id`, `user_id`, `text`).
  - `Slack Interaction`: block_action payload samples for order modal submissions.
  - `Admin`: `/coffee admin` commands covering enable/disable and reset flows.
- Use the Postman `Pre-request Script` to compute Slack signature (`X-Slack-Signature`, `X-Slack-Request-Timestamp`) via the signing secret.

### Docker Workflow
```bash
docker compose up --build api worker postgres kafka
docker compose ps
docker compose logs -f api worker
docker compose exec postgres psql -U coffeebuddy -c '\dt'
# Health checks
curl -f http://localhost:8080/health/live
curl -f http://localhost:8080/metrics
# Teardown
docker compose down -v
```

### Broker Expectations
- Topics defined in code: `coffeebuddy.run.events`, `coffeebuddy.reminder.events`.
- Local Kafka (Compose) exposes `PLAINTEXT://kafka:9092`; override via `KAFKA_BROKERS`.
- Reminder payload schema: `{ "run_id": UUID, "channel_id": UUID, "runner_slack_id": str, "pickup_time": ISO8601, "reminder_offset_minutes": int, "last_call": bool }`.
- Set ACL principal to `serviceAccount:coffeebuddy` with `READ`/`WRITE` on both topics.

### Docker/Kubernetes Health
- `kubectl rollout status deploy/coffeebuddy-api`
- `kubectl logs deploy/coffeebuddy-worker -f`
- Kong route `/slack/events` must return 2xx for Slack challenge.
- Prometheus scrape config should target `coffeebuddy-api:9464/metrics`.

### Environment Variables
| Variable | Scope | Notes |
| --- | --- | --- |
| `SLACK_SIGNING_SECRET` | API | Mandatory for every request verification. |
| `SLACK_BOT_TOKEN` | API/worker | Used for channel posts and DMs. |
| `DATABASE_URL` | API/worker | Provided via Vault secret mount; load with SQLAlchemy. |
| `KAFKA_BROKERS` | API/worker | Comma-separated `host:port`. |
| `KAFKA_SSL_CA` | optional | Required when brokers enforce TLS. |
| `REMINDER_WORKER_GROUP` | worker | Distinguishes consumer offsets. |
| `CHANNEL_DEFAULT_REMINDER_MINUTES` | API | Applies when channel not configured. |
| `CHANNEL_DEFAULT_RETENTION_DAYS` | API | Governs pruning jobs. |
| `DISABLE_REMINDERS` | optional | Flag to short-circuit reminder scheduling (`true/false`). |
| `LOG_LEVEL` | both | Defaults to `INFO`. |
| `PROMETHEUS_METRICS_PORT` | API | Binds metrics server. |
| `VAULT_ADDR`, `VAULT_ROLE_ID`, `VAULT_SECRET_ID` | both | For AppRole auth when fetching secrets. |
| `OIDC_ISSUER`, `OIDC_AUDIENCE` | API | For Ory token validation on internal calls. |

`.env` loading strategy:
- Local dev: place non-secret defaults in `.env.local`, then `export $(cat .env.local | xargs)`.
- CI/staging/prod: mount via Vault agent or Kubernetes secrets; never commit real values.

### Assumptions
- FastAPI entrypoint `coffeebuddy.api.main:app` exists (aligns with KIT scaffolding).
- Postman collection file path may need regeneration if missing.
- Ports (8080 API, 9464 metrics) follow platform templates; adjust if manifests differ.