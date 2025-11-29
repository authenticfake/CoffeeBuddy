# RELEASE_NOTES

## Version
- v0.9.0 — 2024-04-04

## Scope & Traceability
- REQ-001 Slack run bootstrap
- REQ-002 Order capture & preference reuse
- REQ-003 Run closing, fairness, summaries
- REQ-004 Reminder scheduling & delivery
- REQ-005 Admin channel controls & resets
- REQ-006 Postgres schema & migrations
- REQ-007 Kafka topics & reminder worker plumbing

## Highlights
- End-to-end Slack workflow: `/coffee` slash command through runner DM summary in under 2 seconds P95.
- Deterministic fairness engine with channel-scoped history and transparent summary messaging.
- Kafka-backed reminder pipeline with optional “last call” channel alerts.
- Full admin console via `/coffee admin`, including enable/disable, config, and destructive resets with audit logs.
- Hardened infra: Alembic migrations, Vault-fed DB credentials, declarative Kafka topic specs, Prometheus metrics.

## Breaking Changes
- Legacy `/coffee run` subcommand removed; all run creation uses base `/coffee`.
- Reminder scheduler now exclusively driven by Kafka; any cron-based scripts must be decommissioned.

## Known Issues
- Slack signature verification relies on single-region clock skew (<1 minute); larger drifts may yield false negatives.
- Reminder worker currently single-threaded; high-volume environments may require horizontal scaling.

## Assumptions
- Platform teams provision Kong route, Postgres DB, Kafka topics, Vault paths, and Ory clients per SPEC before deployment.

## Metadata
- Tags: `release/v0.9.0`, `reqs/001-007`