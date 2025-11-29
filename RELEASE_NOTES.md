## v1.0.0 — 2024-05-28

### Included Scope
- REQ-001 Slack run bootstrap pipeline
- REQ-002 Order capture and preference reuse
- REQ-003 Run close fairness and summary
- REQ-004 Reminder scheduling and delivery
- REQ-005 Admin channel controls and resets
- REQ-006 Postgres schema and retention policies
- REQ-007 Kafka topics and reminder worker plumbing

### Highlights
- End-to-end `/coffee` workflow: start, order, close, summarize, and DM runner within pilot latency targets.
- Persistent preferences and fairness algorithm ensure transparent runner rotations.
- Kafka-backed reminder system with retry/backoff plus Prometheus metrics.
- Admin console with enable/disable, config tuning, and data reset (with audit logging).
- Hardened infra layer: Alembic migrations, Vault-driven DB credentials, Kafka ACL documentation.

### Breaking Changes
- Requires new Postgres schema (`coffeebuddy_core`) and Kafka topics; run migrations and coordinate platform provisioning before deploying.
- Channels disabled via admin command now reject `/coffee` entirely (previous versions ignored flag).

### Known Issues
- No automated scaling of reminder workers; horizontal scaling must be configured manually.
- Postman collection must be regenerated manually from OpenAPI before each release.