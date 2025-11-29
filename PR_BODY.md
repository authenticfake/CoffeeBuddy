# FINALIZE

## Title
Release v1.0.0 — CoffeeBuddy pilot-ready stack

## Summary
- Implements complete Slack run flow with persistence, fairness, admin controls, and reminders per SPEC/PLAN.
- Adds Postgres schema/migrations, Kafka topic configs, and Vault-backed infra helpers.
- Provides documentation (README, HOWTO, release notes, ops checklists) for deployment and support.

## Scope
- Includes REQ-001 through REQ-007.
- No changes beyond CoffeeBuddy services (no external dependencies introduced).

## Testing
- `pytest -q`
- `docker compose -f deploy/docker-compose.yml up --build` (manual smoke of `/coffee` flow and reminder worker).
- Manual Postman smoke tests for slash command, order modal, admin disable/enable.

## Risks
- Reminder worker timing depends on Kafka stability; monitor `reminder_sent` lag.
- Slack app misconfiguration (scopes/signing secret) will block interactions; verify during rollout.

## Rollback Plan
- Scale down CoffeeBuddy deployment and reminder worker.
- Re-tag image to previous stable release (e.g., `v0.9.x`) and redeploy via Helm/Argo.
- Restore database snapshot taken prior to migration `V0001` if schema regressions occur.

## Assumptions
- Target environment already exposes Kong route and Vault secrets; adjust rollout tasks if not.