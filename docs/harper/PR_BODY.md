## PR_BODY

### Title
CoffeeBuddy v0.4.0 — Full Slack run lifecycle with reminders

### Summary
- Implements Slack slash command → order capture → fair runner selection → summary and DM delivery.
- Adds Kafka-backed reminder scheduling/worker pipeline plus observability metrics.
- Introduces admin UX for enable/disable, config tuning, and channel data resets.
- Finalizes Postgres schema, Alembic migrations, and Kafka topic provisioning utilities.

### Scope
- ✅ REQ-001 through REQ-007
- Includes tests for handlers, fairness, reminders, admin, infra modules.

### Testing Evidence
- `pytest -q`
- `docker compose up` + manual `/coffee` flow in dev Slack workspace.
- Verified reminder worker sends DM within ±1 minute offset.
- `curl /health/* /metrics` success responses.

### Risks
- Slack signature or OAuth misconfiguration blocks traffic (monitor 401s).
- Reminder timing dependent on Kafka lag; watch `reminder_lag_seconds` metric.
- Data reset is destructive; ensure admin confirmation flows communicated.

### Rollback Plan
1. `kubectl rollout undo deployment/coffeebuddy-api`.
2. Scale reminder worker to zero.
3. Re-point Kong route to previous tag.
4. Restore Postgres snapshot if schema regressions detected.