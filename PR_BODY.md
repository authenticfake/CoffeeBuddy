## PR_BODY

**Title:** CoffeeBuddy slice-1 GA: Slack runs, orders, fairness, reminders, admin, and infra hardening

## Summary
- Delivers full CoffeeBuddy workflow from `/coffee` initiation through runner summary and reminders.
- Adds channel admin controls with audited enable/disable, retention, and reset operations.
- Finalizes infra: Alembic migrations, Vault-aware DB sessions, declarative Kafka topics, reminder worker harness, and Prometheus metrics.

## Scope
- REQ-001 through REQ-007 inclusive.
- FastAPI API service, Kafka reminder worker, Postgres schema, Slack UX, and admin tooling.

## Testing Evidence
- `poetry run pytest -q` (attach CI artifact).
- `docker compose up --build` smoke with Slack payload replay (manual verification screenshot/logs).
- `kafka-consumer-groups --bootstrap-server $KAFKA_BROKERS --describe --group coffeebuddy-reminders` showing healthy lag.
- Postman run exporting `/coffee` happy-path transcript.

## Risks
- Reminder timing sensitive to broker/worker clock drift.
- Admin data reset locks tables briefly; coordinate during off-peak usage.
- Slack rate limits could be hit if reminders retried aggressively; monitor `coffeebuddy_errors_total{type="slack_rate_limit"}`.

## Rollback Plan
1. Scale reminder worker to zero to stop new reminders.
2. Roll back API deployment using `kubectl rollout undo deploy/coffeebuddy-api --to-revision=<prev>`.
3. Revert database migrations via `alembic downgrade -1` only if strictly necessary (risk of data loss).
4. Re-apply previous Kafka consumer version and verify health probes before re-enabling slash commands.

## Assumptions
- Slack app credentials, Vault roles, and Kafka ACLs already provisioned in target environment.