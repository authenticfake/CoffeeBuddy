# REQ-005 — Admin channel controls and resets

## Overview
This KIT slice introduces the foundational admin orchestration layer for CoffeeBuddy. It focuses on the `/coffee admin` workflow so authorized actors can enable/disable channels, tune reminder/fairness settings, and trigger channel-level data resets while leaving a durable audit trail.

## Modules
- `coffeebuddy.api.admin.service.AdminService` — coordinates authorization, validation, persistence changes, and audit logging for admin actions.
- `coffeebuddy.api.admin.authorizer.SlackAdminAuthorizer` — reusable policy that checks Slack roles plus the `COFFEEBUDDY_ADMIN_USER_IDS` allow-list.
- `coffeebuddy.api.admin.models` — DTOs for actors, config patches, and response shapes.
- `coffeebuddy.core.audit.AdminAuditLogger` — shared helper that persists `ChannelAdminAction` rows for compliance.

All modules compose with the shared ORM models defined in REQ-006 (`coffeebuddy.infra.db.models`).

## Configuration
- `COFFEEBUDDY_ADMIN_USER_IDS` — comma-separated Slack user IDs that are always authorized for admin operations (in addition to Slack roles `admin`/`owner`).
- Bounds enforced server-side:
  - `reminder_offset_minutes`: 1–60
  - `fairness_window_runs`: 1–50
  - `data_retention_days`: 30–365
  - `last_call_lead_minutes`: 1–30 (required when enabling last-call reminders if no previous value exists)

## Running tests
```bash
pip install -r runs/kit/REQ-005/requirements.txt
PYTHONPATH=runs/kit/REQ-005/src pytest -q runs/kit/REQ-005/test
```

## Future work
- Wire AdminService into the Slack slash command handler (REQ-001) to surface interactive admin UIs.
- Extend audit metadata once channel-scoped admin role mappings are available.
- Add resilience/retries around Vault/DB connectivity per platform standards.

KIT Iteration Log
-----------------
- **Targeted REQ-IDs:** REQ-005 (admin channel controls). Focused per PLAN dependency graph after REQ-001/006 foundations.
- **In Scope:** Admin authorization policy, config updates, enable/disable toggles, data reset orchestration, audit logging, and unit tests.
- **Out of Scope:** Slack command wiring/UI, additional infra hooks, external integrations.
- **Tests:** `PYTHONPATH=runs/kit/REQ-005/src pytest -q runs/kit/REQ-005/test`
- **Prerequisites:** Python 3.12, ability to install `sqlalchemy`/`pytest`, no external services needed.
- **Dependencies & Mocks:** SQLite in-memory DB (via SQLAlchemy) stands in for Postgres during tests; Vault/Slack/Kafka not exercised.
- **Product Owner Notes:** Validation bounds align with SPEC (reminder offset 1–60, fairness 1–50, retention 30–365). Last-call lead minutes required when enabling reminders with no previous value.
- **RAG Citations:** Database schema & models referenced from `runs/kit/REQ-006/src/storage/sql/V0001.up.sql` and `runs/kit/REQ-006/src/coffeebuddy/infra/db/models.py` to stay consistent with persistence layer expectations.

```json
{
  "index": [
    {
      "req": "REQ-005",
      "src": [
        "runs/kit/REQ-005/src/coffeebuddy/api/admin",
        "runs/kit/REQ-005/src/coffeebuddy/core/audit"
      ],
      "tests": [
        "runs/kit/REQ-005/test/test_admin_service.py"
      ]
    }
  ]
}