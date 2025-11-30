## HOWTO_RUN

### CLI Services
- **API**: `uvicorn coffeebuddy.app:app --host 0.0.0.0 --port 8000`
- **Reminder worker**: `python -m coffeebuddy.jobs.reminders.worker`
- **Background scheduler (if separate loop)**: `python -m coffeebuddy.jobs.reminders.scheduler`

All commands expect a configured virtualenv plus exported env vars (see below).

### API & Postman
1. Import `postman/CoffeeBuddy.postman_collection.json`.
2. Folders:
   - `Slack Slash Command` → `POST /slack/command`.
   - `Slack Interaction` → `POST /slack/interaction`.
   - `Admin` → `/slack/admin`.
   - `Ops` → `/health/live`, `/health/ready`, `/metrics`.
3. Set collection variables:
   - `base_url` = `http://localhost:8000`.
   - `slack_signature`, `timestamp`, `payload` for signed requests (pre-script provided).

### Docker Workflow
```bash
docker compose up --build api reminder-worker postgres kafka
docker compose ps
docker compose logs -f api reminder-worker
curl -f http://localhost:8000/health/ready
docker compose down -v
```
Health checks wired to Kubernetes probes; compose uses same endpoints.

### Broker Setup
- Local: docker compose service `kafka` pre-configures `coffeebuddy.run.events` and `coffeebuddy.reminder.events`.
- Remote: set `KAFKA_BROKERS`, `KAFKA_SASL_*`, and ensure ACLs per `src/coffeebuddy/infra/kafka/topics.py`.
- Topics:
  - `coffeebuddy.run.events`
  - `coffeebuddy.reminder.events`
- Reminder worker consumes reminder events; API produces run/reminder payloads.

### Environment Variables
- Required: `SLACK_SIGNING_SECRET`, `SLACK_BOT_TOKEN`, `DATABASE_URL`, `KAFKA_BROKERS`.
- Optional: `KAFKA_SASL_*`, `REMINDER_CONCURRENCY`, `REMINDER_OFFSET_MINUTES`, `FAIRNESS_WINDOW_RUNS`, `PROMETHEUS_MULTIPROC_DIR`, `LOG_LEVEL`.
- Strategy:
  - Dev: copy `.env.example` to `.env` and load via `dotenv` or `direnv`.
  - Prod: mount secrets from Vault adapters; never commit .env with secrets.