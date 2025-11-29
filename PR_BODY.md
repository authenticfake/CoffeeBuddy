# PR_BODY

## Title
CoffeeBuddy v0.9.0 — Pilot-ready Slack runs, reminders, and admin controls

## Summary
- Delivered full `/coffee` workflow with order capture, fairness-based runner assignment, and DM summaries.
- Added Kafka-backed reminder scheduler, configurable per channel.
- Built `/coffee admin` channel controls, data reset, and audit logging.
- Finalized Postgres schema/migrations plus Kafka topic definitions and reminder worker harness.
- Hardened observability via Prometheus metrics and structured logs.

## Scope (REQ IDs)
- REQ-001 through REQ-007 (see RELEASE_NOTES for detail)

## Testing
- `pytest -q` (unit + integration) — PASS
- `ruff check .` — PASS
- `mypy src` — PASS
- `docker compose up --build` (smoke) — PASS
- Manual Postman run: slash command → order modal → close → reminder DM (mock Slack) — PASS

## Risks
- Slack signature validation sensitive to clock drift; monitor NTP sync in clusters.
- Reminder worker single consumer may lag if reminder volume spikes; add autoscaling if pilot load grows.
- Admin disable relies on Slack role mapping; discrepancies could block legitimate admins.

## Rollback Plan
1. Redeploy previous Docker image tag `coffeebuddy:v0.8.x`.
2. Run `alembic downgrade -1` if schema changes must revert (data loss risk acknowledged).
3. Revert Kafka consumer deployment and delete new topics (if unused).
4. Restore Vault secrets snapshot if new paths break prior apps.
5. Notify Slack workspace owners to reinstall previous app manifest if scopes changed.

## Assumptions
- Platform change windows available for Kong route updates and Kafka topic provisioning.