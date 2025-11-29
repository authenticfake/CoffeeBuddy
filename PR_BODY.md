## Title
CoffeeBuddy slice-1 GA: Slack runs, orders, fairness, reminders, admin, and infra foundations

## Summary
- Implements end-to-end `/coffee` workflow with order collection, fairness-based runner assignment, summaries, and DM notifications.
- Adds Kafka-driven reminder scheduling plus retry/backoff and Prometheus metrics.
- Delivers admin console, audit logging, retention policies, Alembic migrations, and Kafka topic plumbing.

## Scope
- REQ-001 through REQ-007 (see RELEASE_NOTES for detail).
- No changes beyond SPEC.md and PLAN.md scope; payments, multi-tenant, and non-Slack channels remain out of scope.

## Test Evidence
- `poetry run pytest -q`
- `poetry run ruff check src`
- `poetry run mypy src`
- `docker compose up --build api worker db kafka` (manual validation of `/health/ready`, `/metrics`, and reminder DM logs)
- Kafka smoke test via `kafkacat` confirming `coffeebuddy.run.events` and `coffeebuddy.reminder.events` payloads.

## Risks
- Kafka topic provisioning/ACLs must match `coffeebuddy.infra.kafka` defaults before deploy; mismatches break reminders.
- Slack app configuration drift (signing secret or scopes) causes 401/invalid signature errors; coordinate with IT before rollout.
- Reminder worker currently single-threaded; high-volume pilots may need horizontal scaling per TODO_NEXT.

## Rollback Plan
1. Scale CoffeeBuddy deployment to zero replicas and stop reminder worker.
2. Revert database schema via `alembic downgrade -1` if necessary (ensure data backup beforehand).
3. Restore previous container image/tag in Kubernetes and re-enable traffic through Kong route once health probes pass.