# HOWTO_RUN

## CLI (Local Dev)
1. Bootstrap environment:
   ```bash
   python -m venv .venv && source .venv/bin/activate
   pip install -e .[dev]
   export SLACK_SIGNING_SECRET=xxx
   export SLACK_BOT_TOKEN=xoxb-...
   export DATABASE_URL=postgresql+psycopg://coffeebuddy:pass@localhost:5432/coffeebuddy
   export KAFKA_BOOTSTRAP=localhost:9092
   ```
2. Apply migrations:
   ```bash
   alembic upgrade head
   ```
3. Run FastAPI service:
   ```bash
   uvicorn coffeebuddy.main:app --host 0.0.0.0 --port 8080 --reload
   ```
4. Start reminder worker (separate shell):
   ```bash
   python -m coffeebuddy.jobs.reminders.worker
   ```

## API / Postman
- Import `docs/postman/CoffeeBuddy.postman_collection.json`.
- Environments:
  - `local`: `base_url=http://localhost:8080`.
- Key requests:
  - `POST /slack/commands` (slash command simulation).
  - `POST /slack/interactions` (order modal submission).
  - `GET /health/ready`.
  - `GET /metrics`.
- Use Postman pre-request script to compute Slack signature (sample script included in collection).

## Docker Compose
```bash
docker compose up --build
```
Services:
- `app`: FastAPI + Slack handlers on `:8080`.
- `db`: Postgres seeded with schema.
- `kafka`: Single-node broker + schema registry stub (if enabled).

Health checks:
- `curl -f http://localhost:8080/health/live`
- `docker compose logs app | grep "application startup complete"`

Teardown:
```bash
docker compose down -v
```

## Broker Guidance
- Default topics reference `coffeebuddy.run.events` and `coffeebuddy.reminder.events`.
- Local compose uses plaintext Kafka; production expects SASL/SCRAM via `KAFKA_SASL_JAAS`.
- Reminder worker consumes `coffeebuddy.reminder.events` and produces `reminder_sent` records back onto `coffeebuddy.run.events` for analytics.

## Env Vars & Loading
- Required: `SLACK_SIGNING_SECRET`, `SLACK_BOT_TOKEN`, `DATABASE_URL`, `KAFKA_BOOTSTRAP`.
- Optional: `KAFKA_SASL_JAAS`, `VAULT_ADDR`, `VAULT_TOKEN`, `PROMETHEUS_MULTIPROC_DIR`, `RUN_FAIRNESS_WINDOW`, `REMINDER_OFFSET_DEFAULT`, `DISABLE_REMINDERS`.
- Local `.env` supported via `python-dotenv` in `coffeebuddy.settings`. Create `.env` (not committed) and the app auto-loads if present.

## Services
- FastAPI app exposes:
  - `/slack/commands` (slash)
  - `/slack/interactions` (interactive)
  - `/coffee/admin` (internal admin router used via Slack)
  - `/health/live`, `/health/ready`, `/metrics`
- Reminder worker is a long-running process; ensure it is supervised (systemd/K8s Deployment) and configured with same env as API (for DB + Slack DM calls).

## Assumptions
- Slack requests arrive via Kong; in local dev, bypass with ngrok or Slack “Request URLs” pointed at developer laptop.
- Ory tokens supplied automatically in cluster; absent locally (flows disabled in dev).