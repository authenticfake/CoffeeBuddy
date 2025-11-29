# FINALIZE

## Version
- `v1.0.0` — 2025-01-14

## Scope & REQ Coverage
- ✅ REQ-001 Slack run bootstrap
- ✅ REQ-002 Order capture & preferences
- ✅ REQ-003 Run close fairness & summaries
- ✅ REQ-004 Reminder scheduling & delivery
- ✅ REQ-005 Admin controls & resets
- ✅ REQ-006 Postgres schema & retention
- ✅ REQ-007 Kafka topics & reminder plumbing

## Highlights
- End-to-end Slack workflow from `/coffee` initiation through runner DM with fairness transparency.
- Kafka-backed reminder scheduler/worker with ±1 minute SLA and failure retries.
- Channel-scoped admin UI enforcing authorization, data retention, and disablement policies.
- Hardened Postgres schema/migrations plus Vault-backed DB session factory.
- Kafka topic definitions, ACL notes, and consumer metrics aligned with platform requirements.

## Breaking Changes
- Channel records now enforce retention/fairness defaults; existing data must run migration `V0001`.
- `/coffee` commands issued in disabled channels receive immediate rejection and do not create runs.

## Known Issues
- Reminder backfill CLI requires manual invocation after Kafka outages; future automation tracked in backlog.
- No automated Slack workspace provisioning; manual app install remains necessary per environment.

## Tagging Guidance
- Tag commits that include these artifacts with `v1.0.0`.
- Upstream services consuming Kafka events should align their deployments to the same tag to avoid schema drift.

## Assumptions
- Deployment date aligns with tag creation; adjust if release is staged later.