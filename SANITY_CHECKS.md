# SANITY_CHECKS

## Checklist
- [ ] `docker compose config` succeeds (valid compose file).
- [ ] `poetry check` or `pip check` passes (dep graph consistent).
- [ ] `ruff check .` reports no errors.
- [ ] `mypy src` passes (or documented ignores).
- [ ] `pytest -q` returns exit code 0 with ≥80% coverage.
- [ ] `uvicorn coffeebuddy.main:app --help` works (entrypoint importable).
- [ ] `curl -f http://localhost:8080/health/ready` after startup.
- [ ] `curl -f http://localhost:8080/metrics | grep coffeebuddy_runs_total`.
- [ ] Postman “Slash command” request returns 200 with mock signature.
- [ ] Reminder worker log shows “consumer started” and no Kafka auth errors.

## Commands & Expected Output
- `docker compose up --build` → App logs “Application startup complete”.
- `pytest -q` → `n passed, 0 failed`.
- `alembic upgrade head` → “INFO  Running upgrade  -> head”.
- `python -m coffeebuddy.jobs.reminders.worker` → “Connected to coffeebuddy.reminder.events”.
- `kafkacat -L -b $KAFKA_BOOTSTRAP | grep coffeebuddy.run.events` → topic visible.

## Common Fixes
- Slack signature mismatch: ensure `SLACK_SIGNING_SECRET` matches workspace app and machine clock is synced.
- DB connection failure: confirm Postgres accepts connections (compose `db` healthy) and `DATABASE_URL` uses psycopg driver.
- Kafka auth failure: set `KAFKA_SASL_JAAS` and `KAFKA_SECURITY_PROTOCOL` to `SASL_SSL` when using secured clusters.
- Reminder worker idle: verify runs include `pickup_time` and channel reminders not disabled; check Kafka topic for enqueued payloads.
- Admin command denied: user must be Slack channel owner or whitelisted ID in `CHANNEL_ADMIN_IDS` config.

## Assumptions
- Developer has local Kafka tooling (e.g., `kafkacat`) when running broker checks.