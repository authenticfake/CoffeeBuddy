## RELEASE_NOTES

**Version:** v0.9.0  
**Date:** 2025-02-14

### Included Scope
- REQ-001 Slack run bootstrap (done)
- REQ-002 Order capture & preferences (done)
- REQ-003 Run close fairness & summary (done)
- REQ-004 Reminder scheduling & delivery (done)
- REQ-005 Admin channel controls & resets (done)
- REQ-006 Postgres schema & retention (done)
- REQ-007 Kafka topics & reminder plumbing (done)

### Highlights
- End-to-end Slack workflow from `/coffee` kickoff through interactive orders and fair runner assignment.
- Kafka-backed reminder pipeline with configurable offsets and last-call channel nudges.
- Channel-level admin console with enable/disable, retention tuning, and audited data resets.
- Hardened infra layer: Alembic migrations, Vault-aware DB sessions, declarative Kafka topics, Prometheus metrics.

### Breaking Changes
- Channels disabled via `/coffee admin` now block slash commands before DB writes—ensure ops run data reset before re-enabling if historical runs are needed.
- Reminder worker contract updated to include channel config snapshot; custom consumers must handle the extended schema.

### Known Issues
- Slack modal localization limited to English.
- Reminder tolerance relies on Kafka consumer clock; drift beyond ±45s requires infra NTP alignment.
- Admin data reset currently synchronous and may take several seconds on large histories; monitor API timeouts.

### Tags / Version Metadata
- git tag recommendation: `v0.9.0`