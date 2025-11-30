## SANITY_CHECKS

### Command Checklist
- `docker compose config` → validates compose syntax.
- `poetry run uvicorn coffeebuddy.api.main:app --help` → confirms FastAPI entrypoint imports.
- `curl -f http://localhost:8080/health/live` → API liveness.
- `curl -f http://localhost:8080/metrics | head` → Prometheus endpoint.
- `poetry run pytest -q` → unit/integration suite.
- `poetry run ruff check src tests` → lint status.
- `poetry run mypy src` → type coverage (if stubs complete).
- `kafka-topics --bootstrap-server $KAFKA_BROKERS --describe --topic coffeebuddy.reminder.events` → topic existence.
- `poetry run python -m coffeebuddy.jobs.reminders.consumer --dry-run` → reminder worker wiring.

### Expected Outputs & Fixes
- **pytest** should exit 0 with ≥80% coverage; if DB tests fail, ensure `DATABASE_URL` points to local Postgres and migrations applied.
- **ruff/mypy** should exit 0; missing stubs typically resolved by adding `py.typed` or ignoring specific Slack SDK modules.
- **Health endpoints** return `{"status":"ok"}` JSON; failures often due to Vault secrets missing—check env injection.
- **Kafka describe** should show partitions=3, replication=3; mismatches require platform ticket referencing `coffeebuddy.run.events`.
- **Reminder dry-run** logs `scheduled reminder` entries; if it blocks, verify `KAFKA_BROKERS` reachable and ACLs applied.

### Postman / API sanity
- Slash command request should return 200 with JSON body `{"response_type":"ephemeral"...}`.
- Interaction payload should update run message blocks within 2 seconds; 401 errors imply invalid Slack signature headers.

### Assumptions
- Local scripts executed from repo root with Poetry virtualenv active.
- Kafka CLI tooling available in PATH for local verification.