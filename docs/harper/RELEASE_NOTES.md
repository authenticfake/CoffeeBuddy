## RELEASE_NOTES

### Version
- `v0.4.0` — 2024-05-19

### Scope & REQ Coverage
- REQ-001 Slack run bootstrap ✅
- REQ-002 Order capture & preferences ✅
- REQ-003 Run close fairness & summary ✅
- REQ-004 Reminder scheduling & delivery ✅
- REQ-005 Admin channel controls ✅
- REQ-006 Postgres schema & retention ✅
- REQ-007 Kafka topics & reminder plumbing ✅

### Highlights
- End-to-end Slack workflow from `/coffee` through auto runner assignment and reminder DMs.
- Kafka-backed reminder job with retry/backoff instrumentation.
- Channel-level admin configuration, disablement, and data reset with audit logging.
- Hardened Postgres schema + Alembic migrations, Vault-backed session factory.
- Prometheus metrics plus Kafka connectivity probes for ops visibility.

### Breaking Changes
- Existing databases must run migration `V0001` (drops legacy tables if structure diverged).
- Topic names standardized; older consumers must adopt `coffeebuddy.reminder.events`.

### Known Issues
- Reminder scheduler currently shares codebase logging config; noisy logs under DEBUG (set `LOG_LEVEL=INFO`).
- No automated Slack slash command smoke runner; manual verification still required after deploy.

### Metadata
- Tag suggestion: `git tag v0.4.0`
- Docker image: `registry.internal/coffee-buddy/api:v0.4.0`