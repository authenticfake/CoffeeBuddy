# PLAN — coffeebuddy

## Plan Snapshot

- **Counts:** total 7 / open 7 / done 0 / deferred 0
- **Progress:** 0%
- **Checklist:**
  - [ ] SPEC aligned
  - [ ] Prior REQ reconciled
  - [ ] Dependencies mapped
  - [ ] KIT-readiness per REQ confirmed

## Tracks & Scope Boundaries

- **Tracks:** App (Slack UX, domain logic) and Infra (data, platform, observability). Infra REQs unblock App but remain minimal.
- **Out of scope / Deferred:** payment/tipping, multi-workspace, external analytics, non-Slack clients, AI personalization, production-grade multi-tenant controls.

## Module/Package & Namespace Plan (per KIT)

- **Slice `runs` (`app.slack.runs`, shared util `app.shared.auth`):** REQ-001 owns slash command handler and run state transitions; new helpers must live under `app.slack.runs`. It reuses repositories from `data.persistence`.
- **Slice `orders` (`app.slack.orders`):** REQ-002 manages order modals, last-order reuse, and validations; only extends existing modules.
- **Slice `fairness` (`app.slack.fairness`):** REQ-003 extends run closing to calculate runner selection and summary messaging; must integrate with `app.slack.runs` services.
- **Slice `reminders` (`app.kafka.reminders`):** REQ-004 introduces Kafka producers/consumers plus schedulers; it may add submodules `scheduler` and `handlers` but must reuse repos/types.
- **Slice `admin` (`app.slack.admin`):** REQ-006 handles admin slash flows, channel config mutations, and audits using `data.config`.
- **Infra Modules:**
  - `data.persistence` (REQ-005) defines SQL migrations, ORM models, and repository interfaces for runs, orders, preferences, runner stats, channel config, and audit logs. App layers must depend on these repositories only.
  - `infra.platform` (REQ-007) configures Vault secret loading, Ory token validation, Kong route contract validation, readiness/liveness probes, logging, and Prometheus metrics registration. App code must call these shared utilities rather than duplicating setup.
- **Shared Modules:** `app.shared.slack` (signature verification, Slack client), `app.shared.events` (Kafka payload DTOs), `app.shared.metrics`. App REQs extend rather than recreate these modules.

## REQ-IDs Table

| ID | Title | Acceptance (≤3 bullets) | DependsOn [IDs] | Track | Status |
| --- | --- | --- | --- | --- | --- |
| REQ-001 | Slash command run lifecycle | `/coffee` ack under 2s with interactive message<br>Run records persisted with state machine<br>Close control validates permissions and status | REQ-005 | App | open |
| REQ-002 | Order capture and preferences | Modal collects orders with validation<br>“Use last order” replays stored preference<br>Edits/cancels reflected in channel message counts | REQ-001, REQ-005 | App | open |
| REQ-003 | Runner fairness and summaries | Fairness rule selects runner with explanation<br>Summary posted in channel plus runner DM<br>Runner stats updated atomically on close | REQ-001, REQ-002, REQ-005 | App | open |
| REQ-004 | Reminder scheduling via Kafka | Run events emitted to Kafka topics<br>Reminder consumer schedules DM/last-call<br>Channel config toggles reminders on/off | REQ-001, REQ-005 | App | open |
| REQ-005 | Data persistence foundations | SQL migrations cover all entities<br>Repository layer enforces retention windows<br>Channel config defaults seeded per SPEC | | Infra | open |
| REQ-006 | Admin flows and config governance | `/coffee admin` gated by Slack roles<br>Enable/disable and config updates persisted<br>Data reset wipes runs/orders/prefs per channel | REQ-005 | App | open |
| REQ-007 | Platform integration & observability | Vault/Ory/Kong wiring centralized<br>Prometheus metrics and histograms exposed<br>Structured logging with correlation IDs + probes | REQ-005 | Infra | open |

### Acceptance — REQ-001
- Slash command endpoint verifies Slack signatures and responds within 2 seconds with an interactive run message containing run metadata, controls, and correlation ID.
- Run creation persists channel, initiator, pickup metadata, and status=open using repositories from `data.persistence`, emitting `run_created`.
- Close control validates caller authority, ensures run is open, and transitions to closing workflow while preventing concurrent closes via optimistic locks.
- Public channel message stays updated with order counts and buttons by referencing run ID, with retries on transient Slack API failures logged.
- Errors (invalid syntax, disabled channel, missing scopes) produce ephemeral Slack hints and log structured reasons without revealing secrets.

### Acceptance — REQ-002
- “Place order” button opens a Slack modal collecting drink text plus optional notes, validates payload, and stores or updates the `Order` tied to user/run.
- “Use last order” pulls the latest confirmed preference for that user/channel, writes a new `Order`, and stamps `UserPreference.last_used_at`.
- Users can edit or cancel orders before close; channel message and order roster reflect changes within one interaction cycle.
- Duplicate active orders for the same user/run are prevented through transactional guards, returning clear Slack errors if attempted.
- Updating a confirmed order refreshes the stored preference so future runs surface it by default.

### Acceptance — REQ-003
- On run close, fairness service gathers eligible participants, excludes last runner unless opt-in flag, and selects the user with lowest `runs_served_count`, then earliest `last_run_at`.
- Runner assignment, run closure, runner stats increment, and summary posting occur within a single transaction + post-commit Slack send to avoid partial states.
- Summary message lists runner, pickup note, participants, and per-order text; explanation line cites fairness rule inputs.
- Runner receives DM with identical summary plus total item count; delivery failures are surfaced in logs and metrics.
- Kafka events `run_closed` and `runner_assigned` carry runner metadata and fairness window stats for downstream consumers.

### Acceptance — REQ-004
- Run creation emits `run_created` and optional `reminder_scheduled` events to Kafka using shared producer with retry/backoff and metrics for failures.
- Reminder scheduler consumes events, calculates trigger time from pickup minus channel offset, and persists pending reminders to avoid duplicates.
- When trigger fires, runner DM and optional channel “last call” message are sent, acknowledging success/failure in Kafka `reminder_sent` events.
- Channel-level config toggles reminders and offset minutes, enforced before scheduling; disabled channels skip scheduler work with audit logs.
- End-to-end reminder latency remains within ±1 minute of target, validated via metrics bucket or integration test harness.

### Acceptance — REQ-005
- Alembic (or equivalent) migrations create tables for User, Channel, Run, Order, UserPreference, RunnerStats, ChannelAdminAction with indices matching access patterns.
- Repository layer enforces channel-scoped data retention (default 90 days, configurable) via scheduled purge hooks and guards against cross-channel leakage.
- Seed defaults for reminder offsets and fairness window values are idempotent and configurable via environment variables sourced from Vault.
- Transaction helper utilities expose unit-of-work boundaries for App slices, supporting optimistic concurrency and soft deletes where needed.
- Unit tests cover CRUD and retention logic against a Postgres test container, ensuring referential integrity and cascade expectations.

### Acceptance — REQ-006
- `/coffee admin` slash command verifies Slack user role or allowlist before showing interactive admin menu; unauthorized requests return polite denial.
- Channel enable/disable toggles stored flag, logs `ChannelAdminAction`, and updates cached state so `/coffee` respects status immediately.
- Admins can update reminder offset, fairness window, and retention values within global bounds; invalid inputs prompt inline validation errors.
- Data reset workflow deletes or anonymizes runs, orders, preferences, and runner stats for the channel, emits audit log, and communicates outcome in Slack.
- All admin actions surface confirmation messages with changed values and are queryable via repository methods for audits.

### Acceptance — REQ-007
- Service startup loads Slack tokens, signing secret, DB creds from Vault once, never logs them, and refreshes if rotation signals occur.
- Ory/OIDC validation middleware ensures internal calls possess required scopes before hitting business handlers; failures return structured 401 logs.
- Kong ingress contract documented and validated via integration smoke test ensuring correct paths, timeouts, and Slack IP allowlists.
- Prometheus `/metrics` endpoint exposes counters and histograms for runs, interactions, errors, reminder timings, with labels aligned to SPEC.
- Liveness/readiness probes check core loops, DB, Kafka, and Vault connectivity; structured JSON logging attaches correlation IDs and severity fields.

## Dependency Graph

- REQ-001 -> REQ-005
- REQ-002 -> REQ-001, REQ-005
- REQ-003 -> REQ-001, REQ-002, REQ-005
- REQ-004 -> REQ-001, REQ-005
- REQ-005 -> (none)
- REQ-006 -> REQ-005
- REQ-007 -> REQ-005

## Iteration Strategy

1. **Batch 1 (S, dependencies cleared):** REQ-005 (Infra foundations) + REQ-007 (platform hooks) to unblock application code. Confidence ±0.5 batch.
2. **Batch 2 (M):** REQ-001 and REQ-002 to enable core run lifecycle and ordering UX atop shared repositories. Confidence ±1 batch.
3. **Batch 3 (M):** REQ-003 and REQ-004 finishing fairness and reminders; requires stable data/events. Confidence ±1 batch.
4. **Batch 4 (S):** REQ-006 admin tooling to finalize governance. Confidence ±0.5 batch.

## Test Strategy

- **REQ-005/007:** Unit tests on repositories, retention jobs, secret loading mocks; integration tests using Postgres container, Vault/Kong stubs; static analysis for migrations.
- **REQ-001/002:** Unit tests for Slack handlers, signature verification, command parsing; integration tests hitting Slack mock server verifying 2s SLA; concurrency tests for order edits.
- **REQ-003:** Deterministic fairness unit tests, DB transaction integration tests, Slack summary snapshot tests.
- **REQ-004:** Kafka contract tests with embedded broker, reminder timing tests, DM sending mocks verifying offsets.
- **REQ-006:** Admin command handler tests, permission matrix tests, data reset integration verifying cascades.
- **Batch-level:** End-to-end scripted scenario (start → orders → close) plus metrics scrape verification; non-functional tests for P95 latency.

## KIT Readiness (per REQ)

- **REQ-001**
  - Paths: `/runs/kit/REQ-001/src/app/slack/runs`, `/runs/kit/REQ-001/test`
  - Root package `app.slack.runs`; reuse `app.shared.slack` from scaffolds.
  - Commands: `pytest tests/slack/runs -m "not slow"`.
  - KIT-functional: yes; Slack mock configs required via `.env.test`.
  - API docs: `/runs/kit/REQ-001/test/api/slack-run.json`.

- **REQ-002**
  - Paths: `/runs/kit/REQ-002/src/app/slack/orders`, `/runs/kit/REQ-002/test`
  - Root namespace `app.slack.orders`; no new top-level packages.
  - Commands: `pytest tests/slack/orders`.
  - KIT-functional: yes; fixtures expect seeded runs/orders from REQ-001.
  - API docs: `/runs/kit/REQ-002/test/api/order-modals.json`.

- **REQ-003**
  - Paths: `/runs/kit/REQ-003/src/app/slack/fairness`, `/runs/kit/REQ-003/test`
  - Namespace `app.slack.fairness`; depends on repositories defined earlier.
  - Commands: `pytest tests/slack/fairness`.
  - KIT-functional: yes; fairness window config provided via `config/test.yaml`.
  - API docs: `/runs/kit/REQ-003/test/api/summary-flow.json`.

- **REQ-004**
  - Paths: `/runs/kit/REQ-004/src/app/kafka/reminders`, `/runs/kit/REQ-004/test`
  - Namespace `app.kafka.reminders`; produce/consume utilities under `app.shared.events`.
  - Commands: `pytest tests/kafka --embedded-broker`.
  - KIT-functional: yes; docker-compose for Kafka at `/runs/kit/REQ-004/test/compose.yaml`.
  - API docs: `/runs/kit/REQ-004/test/api/reminder-events.json`.

- **REQ-005**
  - Paths: `/runs/kit/REQ-005/src/data/persistence`, `/runs/kit/REQ-005/test`
  - Namespace `data.persistence`; migrations under `data/persistence/migrations`.
  - Commands: `pytest tests/data --db-url=postgresql://localhost:5432/test`.
  - KIT-functional: yes; requires Postgres container spun up via `make db-up`.
  - API docs: N/A (database focus).

- **REQ-006**
  - Paths: `/runs/kit/REQ-006/src/app/slack/admin`, `/runs/kit/REQ-006/test`
  - Namespace `app.slack.admin`; extends shared Slack utilities.
  - Commands: `pytest tests/slack/admin`.
  - KIT-functional: yes; admin allowlist fixture at `tests/fixtures/admin_users.json`.
  - API docs: `/runs/kit/REQ-006/test/api/admin-flow.json`.

- **REQ-007**
  - Paths: `/runs/kit/REQ-007/src/infra/platform`, `/runs/kit/REQ-007/test`
  - Namespace `infra.platform`; modules `secrets`, `auth`, `observability`.
  - Commands: `pytest tests/infra`.
  - KIT-functional: yes; requires mock Vault/Ory servers defined in `test/docker-compose.yaml`.
  - API docs: `/runs/kit/REQ-007/test/api/probes.json`.

## Notes

- **Assumptions:** Kafka topic provisioning handled outside KIT; plan assumes topics exist though REQ-004 validates contracts. Slack admin allowlist provided by ops. Vault paths standardized as `secret/data/coffeebuddy/*`.
- **Risks:** Slack rate limits could delay interactive updates; mitigation via retry/backoff built into `app.shared.slack`. Reminder scheduling accuracy depends on cluster clock sync; ensure NTP monitoring.
- **Mitigations:** Early dry-runs against dev Slack workspace; integrate lint/type checks (ruff, mypy) within python lane gate; document data reset impacts for compliance review.

PLAN_END