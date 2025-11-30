# PLAN — coffeebuddy

## Plan Snapshot

- **Counts:** total=7 / open=0 / in_progress=1 / done=6 / deferred=0
- **Progress:** 86% complete
- **Checklist:**
  - [x] SPEC aligned
  - [x] Prior REQ reconciled
  - [x] Dependencies mapped
  - [x] KIT-readiness per REQ confirmed

## Tracks & Scope Boundaries

- **Tracks:** Application (Slack UX, workflows, scheduling) vs Infra (schema, Kafka, platform hooks). App drives user value; Infra only when blocking App.
- **Out of scope / Deferred:** Payments, multi-workspace tenancy, external analytics, non-Slack channels, AI personalization, non-core observability extras.

## Module & Namespace Plan (per KIT)

- **Slice `slack_runs` (App, REQ-001):** Root namespace `coffeebuddy.api.slack_runs`. Owns slash command handlers, run creation, Slack response builders. Must reuse shared DB session helper `coffeebuddy.infra.db`.
- **Slice `orders` (App, REQ-002):** Root namespace `coffeebuddy.core.orders`. Extends existing ORM models under `coffeebuddy.models`. May add `coffeebuddy.services.preferences`, but must consume `coffeebuddy.api.slack_runs` request context utilities.
- **Slice `run_lifecycle` (App, REQ-003):** Root namespace `coffeebuddy.core.runs`. Reuses `coffeebuddy.core.orders` for aggregations and updates `coffeebuddy.services.fairness`. New modules limited to `coffeebuddy.services.fairness`.
- **Slice `reminders` (App, REQ-004):** Root namespace `coffeebuddy.jobs.reminders`. Must consume Kafka client utilities from `coffeebuddy.infra.kafka` and Slack DM helpers from `coffeebuddy.api.slack_runs`.
- **Slice `admin` (App, REQ-005):** Root namespace `coffeebuddy.api.admin`. Shares `coffeebuddy.models` entities, writes audit entries via `coffeebuddy.core.audit`.
- **Infra Module `coffeebuddy.infra.db` (REQ-006):** Defines SQLAlchemy models/migrations under `coffeebuddy.models`. App REQs may extend models but not create alternate persistence layers.
- **Infra Module `coffeebuddy.infra.kafka` (REQ-007):** Provides topic definitions, producer/consumer wrappers, reminder scheduler bindings. App code must import topics/constants from here; no ad-hoc topic names.

## REQ-IDs Table

| ID | Title | Acceptance | DependsOn | Track | Status |
|---|---|---|---|---|---|
| REQ-001 | Slack run bootstrap pipeline | Slash command verified with Slack signing secret before execution<br/>Run row persisted with open status pickup metadata correlation ID<br/>Interactive message posted within 2s showing controls<br/>Optional parameters validated and reflected in Slack response<br/>Kafka run_created event emitted with run identifiers |  | App | done |
| REQ-002 | Order capture and preference reuse | Order modal enforces length and non-empty validation<br/>Order upsert updates participant count in channel message<br/>Use last order pulls preference or errors gracefully<br/>Order edits or cancels prevent duplicate active orders<br/>Confirmed orders refresh channel-scoped preference record | REQ-001 | App | done |
| REQ-003 | Run close fairness and summary | Close action restricted to initiator or admins with clear errors<br/>Fairness picks runner via runs_served_count then last_run_at<br/>Run transitions to closed with runner stats updated transactionally<br/>Channel summary lists metadata runner and participant orders<br/>Runner DM mirrors summary plus totals and reminder info | REQ-001, REQ-002, REQ-006 | App | done |
| REQ-004 | Reminder scheduling and delivery | Runs with pickup time enqueue reminder payloads on Kafka<br/>Runner reminders sent at pickup time minus offset within tolerance<br/>Optional last call channel alerts respect channel settings<br/>Reminder outcomes logged and emitted as metrics<br/>Failed reminders retried with backoff and surfaced in errors | REQ-003, REQ-007 | App | in_progress |
| REQ-005 | Admin channel controls and resets | Admin command verifies Slack roles or configured admins<br/>Config UI updates reminder offset fairness window retention bounds<br/>Config changes persist and emit audit entries<br/>Disabled channels reject new runs with clear notice<br/>Data reset purges channel history and logs action summary | REQ-001, REQ-006 | App | done |
| REQ-006 | Postgres schema and retention policies | Migrations create tables for users channels runs orders preferences stats audits<br/>Retention columns default to 90 days and accept overrides<br/>ORM models expose shared serialization helpers<br/>Vault-sourced DB credentials power resilient session factory<br/>Migration command documented and idempotent for CI |  | Infra | done |
| REQ-007 | Kafka topics and reminder worker plumbing | Kafka topics defined with partitions replication and retention notes<br/>Producer consumer utilities enforce payload schemas and IDs<br/>Reminder worker harness documented with graceful shutdown<br/>Topic ACL needs captured for platform coordination<br/>Kafka connectivity metrics exported for Prometheus |  | Infra | done |

zation helpers<br/>Vault-sourced DB credentials power resilient session factory<br/>Migration command documented and idempotent for CI |  | Infra | done |
| REQ-007 | Kafka topics and reminder worker plumbing | Kafka topics defined with partitions replication and retention notes<br/>Producer consumer utilities enforce payload schemas and IDs<br/>Reminder worker harness documented with graceful shutdown<br/>Topic ACL needs captured for platform coordination<br/>Kafka connectivity metrics exported for Prometheus |  | Infra | done |

zation helpers<br/>Vault-sourced DB credentials power resilient session factory<br/>Migration command documented and idempotent for CI |  | Infra | done |
| REQ-007 | Kafka topics and reminder worker plumbing | Kafka topics defined with partitions replication and retention notes<br/>Producer consumer utilities enforce payload schemas and IDs<br/>Reminder worker harness documented with graceful shutdown<br/>Topic ACL needs captured for platform coordination<br/>Kafka connectivity metrics exported for Prometheus |  | Infra | done |

zation helpers<br/>Vault-sourced DB credentials power resilient session factory<br/>Migration command documented and idempotent for CI |  | Infra | done |
| REQ-007 | Kafka topics and reminder worker plumbing | Kafka topics defined with partitions replication and retention notes<br/>Producer consumer utilities enforce payload schemas and IDs<br/>Reminder worker harness documented with graceful shutdown<br/>Topic ACL needs captured for platform coordination<br/>Kafka connectivity metrics exported for Prometheus |  | Infra | in_progress |

zation helpers<br/>Vault-sourced DB credentials power resilient session factory<br/>Migration command documented and idempotent for CI |  | Infra | done |
| REQ-007 | Kafka topics and reminder worker plumbing | Kafka topics defined with partitions replication and retention notes<br/>Producer consumer utilities enforce payload schemas and IDs<br/>Reminder worker harness documented with graceful shutdown<br/>Topic ACL needs captured for platform coordination<br/>Kafka connectivity metrics exported for Prometheus |  | Infra | in_progress |

zation helpers<br/>Vault-sourced DB credentials power resilient session factory<br/>Migration command documented and idempotent for CI |  | Infra | done |
| REQ-007 | Kafka topics and reminder worker plumbing | Kafka topics defined with partitions replication and retention notes<br/>Producer consumer utilities enforce payload schemas and IDs<br/>Reminder worker harness documented with graceful shutdown<br/>Topic ACL needs captured for platform coordination<br/>Kafka connectivity metrics exported for Prometheus |  | Infra | in_progress |

zation helpers<br/>Vault-sourced DB credentials power resilient session factory<br/>Migration command documented and idempotent for CI |  | Infra | done |
| REQ-007 | Kafka topics and reminder worker plumbing | Kafka topics defined with partitions replication and retention notes<br/>Producer consumer utilities enforce payload schemas and IDs<br/>Reminder worker harness documented with graceful shutdown<br/>Topic ACL needs captured for platform coordination<br/>Kafka connectivity metrics exported for Prometheus |  | Infra | in_progress |

zation helpers<br/>Vault-sourced DB credentials power resilient session factory<br/>Migration command documented and idempotent for CI |  | Infra | done |
| REQ-007 | Kafka topics and reminder worker plumbing | Kafka topics defined with partitions replication and retention notes<br/>Producer consumer utilities enforce payload schemas and IDs<br/>Reminder worker harness documented with graceful shutdown<br/>Topic ACL needs captured for platform coordination<br/>Kafka connectivity metrics exported for Prometheus |  | Infra | in_progress |

zation helpers<br/>Vault-sourced DB credentials power resilient session factory<br/>Migration command documented and idempotent for CI |  | Infra | done |
| REQ-007 | Kafka topics and reminder worker plumbing | Kafka topics defined with partitions replication and retention notes<br/>Producer consumer utilities enforce payload schemas and IDs<br/>Reminder worker harness documented with graceful shutdown<br/>Topic ACL needs captured for platform coordination<br/>Kafka connectivity metrics exported for Prometheus |  | Infra | in_progress |

zation helpers<br/>Vault-sourced DB credentials power resilient session factory<br/>Migration command documented and idempotent for CI |  | Infra | done |
| REQ-007 | Kafka topics and reminder worker plumbing | Kafka topics defined with partitions replication and retention notes<br/>Producer consumer utilities enforce payload schemas and IDs<br/>Reminder worker harness documented with graceful shutdown<br/>Topic ACL needs captured for platform coordination<br/>Kafka connectivity metrics exported for Prometheus |  | Infra | in_progress |

zation helpers<br/>Vault-sourced DB credentials power resilient session factory<br/>Migration command documented and idempotent for CI |  | Infra | done |
| REQ-007 | Kafka topics and reminder worker plumbing | Kafka topics defined with partitions replication and retention notes<br/>Producer consumer utilities enforce payload schemas and IDs<br/>Reminder worker harness documented with graceful shutdown<br/>Topic ACL needs captured for platform coordination<br/>Kafka connectivity metrics exported for Prometheus |  | Infra | in_progress |

zation helpers<br/>Vault-sourced DB credentials power resilient session factory<br/>Migration command documented and idempotent for CI |  | Infra | done |
| REQ-007 | Kafka topics and reminder worker plumbing | Kafka topics defined with partitions replication and retention notes<br/>Producer consumer utilities enforce payload schemas and IDs<br/>Reminder worker harness documented with graceful shutdown<br/>Topic ACL needs captured for platform coordination<br/>Kafka connectivity metrics exported for Prometheus |  | Infra | in_progress |

zation helpers<br/>Vault-sourced DB credentials power resilient session factory<br/>Migration command documented and idempotent for CI |  | Infra | in_progress |
| REQ-007 | Kafka topics and reminder worker plumbing | Kafka topics defined with partitions replication and retention notes<br/>Producer consumer utilities enforce payload schemas and IDs<br/>Reminder worker harness documented with graceful shutdown<br/>Topic ACL needs captured for platform coordination<br/>Kafka connectivity metrics exported for Prometheus |  | Infra | in_progress |

zation helpers<br/>Vault-sourced DB credentials power resilient session factory<br/>Migration command documented and idempotent for CI |  | Infra | in_progress |
| REQ-007 | Kafka topics and reminder worker plumbing | Kafka topics defined with partitions replication and retention notes<br/>Producer consumer utilities enforce payload schemas and IDs<br/>Reminder worker harness documented with graceful shutdown<br/>Topic ACL needs captured for platform coordination<br/>Kafka connectivity metrics exported for Prometheus |  | Infra | in_progress |

zation helpers<br/>Vault-sourced DB credentials power resilient session factory<br/>Migration command documented and idempotent for CI |  | Infra | in_progress |
| REQ-007 | Kafka topics and reminder worker plumbing | Kafka topics defined with partitions replication and retention notes<br/>Producer consumer utilities enforce payload schemas and IDs<br/>Reminder worker harness documented with graceful shutdown<br/>Topic ACL needs captured for platform coordination<br/>Kafka connectivity metrics exported for Prometheus |  | Infra | open |

zation helpers<br/>Vault-sourced DB credentials power resilient session factory<br/>Migration command documented and idempotent for CI |  | Infra | in_progress |
| REQ-007 | Kafka topics and reminder worker plumbing | Kafka topics defined with partitions replication and retention notes<br/>Producer consumer utilities enforce payload schemas and IDs<br/>Reminder worker harness documented with graceful shutdown<br/>Topic ACL needs captured for platform coordination<br/>Kafka connectivity metrics exported for Prometheus |  | Infra | open |

zation helpers<br/>Vault-sourced DB credentials power resilient session factory<br/>Migration command documented and idempotent for CI |  | Infra | in_progress |
| REQ-007 | Kafka topics and reminder worker plumbing | Kafka topics defined with partitions replication and retention notes<br/>Producer consumer utilities enforce payload schemas and IDs<br/>Reminder worker harness documented with graceful shutdown<br/>Topic ACL needs captured for platform coordination<br/>Kafka connectivity metrics exported for Prometheus |  | Infra | open |

zation helpers<br/>Vault-sourced DB credentials power resilient session factory<br/>Migration command documented and idempotent for CI |  | Infra | in_progress |
| REQ-007 | Kafka topics and reminder worker plumbing | Kafka topics defined with partitions replication and retention notes<br/>Producer consumer utilities enforce payload schemas and IDs<br/>Reminder worker harness documented with graceful shutdown<br/>Topic ACL needs captured for platform coordination<br/>Kafka connectivity metrics exported for Prometheus |  | Infra | open |

zation helpers<br/>Vault-sourced DB credentials power resilient session factory<br/>Migration command documented and idempotent for CI |  | Infra | in_progress |
| REQ-007 | Kafka topics and reminder worker plumbing | Kafka topics defined with partitions replication and retention notes<br/>Producer consumer utilities enforce payload schemas and IDs<br/>Reminder worker harness documented with graceful shutdown<br/>Topic ACL needs captured for platform coordination<br/>Kafka connectivity metrics exported for Prometheus |  | Infra | open |

zation helpers<br/>Vault-sourced DB credentials power resilient session factory<br/>Migration command documented and idempotent for CI |  | Infra | open |
| REQ-007 | Kafka topics and reminder worker plumbing | Kafka topics defined with partitions replication and retention notes<br/>Producer consumer utilities enforce payload schemas and IDs<br/>Reminder worker harness documented with graceful shutdown<br/>Topic ACL needs captured for platform coordination<br/>Kafka connectivity metrics exported for Prometheus |  | Infra | open |

zes sessions | [] | Infra | open |
| REQ-007 | Kafka topics and reminder worker plumbing | Topics provisioned with ACL notes<br>Producer/consumer wrappers exposed<br>Reminder job harness documented | [] | Infra | open |

### Acceptance — REQ-001
- Slash command `/coffee` verified using Slack signing secret before processing.
- New `Run` row persisted with `open` status, pickup metadata, and correlation ID within a single transaction.
- Slack interactive message posted within 2 seconds, showing run header, order CTA, close control placeholder.
- Optional parameters (pickup time, note) parsed, validated, and reflected in the initial Slack message.
- Kafka `run_created` event emitted with run ID, channel ID, initiator ID.

### Acceptance — REQ-002
- “Place order” action opens modal enforcing max length and non-empty order text.
- Submitting an order upserts `Order` tied to run/user and updates message participant count.
- “Use last order” button fetches stored preference, fails gracefully if none, and records provenance.
- Editing or canceling orders reflects immediately in channel message and DB, preventing multiple active orders per user/run.
- Confirmed order automatically updates `UserPreference.last_order_text` scoped to channel.

### Acceptance — REQ-003
- “Close run” action restricted to initiator or channel admins; unauthorized attempts receive clear Slack error.
- Fairness service selects runner by minimal recent `runs_served_count`, tiebreak on oldest `last_run_at`, avoiding immediate repeats unless opt-in flag set.
- Run transitions from `open` to `closed` within a transaction updating runner stats and final order snapshots.
- Channel summary message lists pickup metadata, runner, and participant orders in deterministic order.
- Runner DM mirrors channel summary plus total drink count and reminder configuration snippet.

### Acceptance — REQ-004
- Runs with pickup time enqueue reminder job payloads on Kafka with reminder timestamp and channel config snapshot.
- Reminder consumer schedules runner DM at `pickup_time - offset` with ±1 minute tolerance, respecting disabled flags.
- Optional “last call” channel reminder triggered when configured, and skipped otherwise.
- Reminder send outcomes logged with correlation ID and emitted as `reminder_sent` metrics/events.
- Failed reminders retried per backoff policy and surfaced in error metrics.

### Acceptance — REQ-005
- `/coffee admin` command verifies user authority via Slack roles or configured admin list before showing options.
- Admin UI allows enabling/disabling channel, adjusting reminder offsets, fairness window, retention days within bounds.
- Config changes persist to `Channel` record, emit audit entry, and confirm via ephemeral Slack message.
- Disabling channel causes subsequent `/coffee` invocations to respond with disabled notice and skip DB writes.
- Data reset operation removes historical runs, orders, preferences, runner stats for the channel and records action summary.

### Acceptance — REQ-006
- SQL migrations create `users`, `channels`, `runs`, `orders`, `user_preferences`, `runner_stats`, `channel_admin_actions` with indexes per data model.
- Retention-related columns (e.g., `data_retention_days`) default to 90 and support overrides per channel.
- ORM models expose serialization helpers reused by App slices without duplicating schema.
- Vault-sourced DB credentials wired into `coffeebuddy.infra.db` session factory with retry/backoff.
- Automated migration command documented and idempotent, runnable in CI and environments.

### Acceptance — REQ-007
- Kafka topics `coffeebuddy.run.events` and `coffeebuddy.reminder.events` defined with partitions/replication per platform standard.
- Producer/consumer utilities expose structured payload schemas and enforce correlation IDs.
- Reminder worker harness documented with polling loop, graceful shutdown, metrics hooks.
- Topic ACL requirements and service principals captured for platform handoff.
- Health metrics for Kafka connectivity exported for Prometheus scraping.

## Dependency Graph

- REQ-001 -> (none)
- REQ-002 -> REQ-001
- REQ-003 -> REQ-001, REQ-002, REQ-006
- REQ-004 -> REQ-003, REQ-007
- REQ-005 -> REQ-001, REQ-006
- REQ-006 -> (none)
- REQ-007 -> (none)

## Iteration Strategy

- **Batch 1 (S):** REQ-006, REQ-007 to unblock persistence and messaging foundations.
- **Batch 2 (M):** REQ-001 plus REQ-002 to enable run creation and ordering flows atop new schema.
- **Batch 3 (M):** REQ-003 and REQ-005 to complete lifecycle closure and admin controls.
- **Batch 4 (S):** REQ-004 to finalize reminder scheduling leveraging Kafka. Confidence ±1 batch.

## Test Strategy

- **REQ-001-002:** Unit tests for Slack handlers, modal validation; integration tests with in-memory DB; contract tests for Slack payload parsing.
- **REQ-003:** Fairness algorithm unit tests covering tie breaks; integration tests verifying runner summaries and status transitions.
- **REQ-004:** Kafka consumer/producer integration using embedded broker; scheduled reminder timing tests; E2E verifying DM payloads (mock Slack).
- **REQ-005:** Permission tests for admin command, reset side effects; audit log assertions.
- **REQ-006:** Migration smoke tests, retention default enforcement tests; DB session factory tests.
- **REQ-007:** Topic schema validation tests, consumer loop behavior under failure; metrics exposure tests.
- **Batch E2E:** Simulated run from start to reminder verifying metrics via Prometheus scrape stub.

## KIT Readiness

- **REQ-001:** `/runs/kit/REQ-001/src/coffeebuddy/api/slack_runs`; tests under `/runs/kit/REQ-001/test`. Use FastAPI + Slack SDK, `pytest`. Lane python. KIT-functional: yes.
- **REQ-002:** `/runs/kit/REQ-002/src/coffeebuddy/core/orders`; tests cover modal handlers/preferences. Lane python. Reuse shared models from REQ-006 scaffolds. KIT-functional: yes.
- **REQ-003:** `/runs/kit/REQ-003/src/coffeebuddy/core/runs` plus `services/fairness`. Tests assert fairness logic, Slack summary builders. Lane python. KIT-functional: yes.
- **REQ-004:** `/runs/kit/REQ-004/src/coffeebuddy/jobs/reminders`. Kafka clients under `coffeebuddy.infra.kafka`. Tests simulate Kafka streams. Lane python. KIT-functional: yes.
- **REQ-005:** `/runs/kit/REQ-005/src/coffeebuddy/api/admin`. Tests for authorization, config persistence, disable/reset states. Lane python. KIT-functional: yes.
- **REQ-006:** `/runs/kit/REQ-006/src/coffeebuddy/infra/db` hosting models/migrations; tests using `pytest` + `alembic` runners under `/test`. Lane sql. KIT-functional: yes.
- **REQ-007:** `/runs/kit/REQ-007/src/coffeebuddy/infra/kafka`; tests verifying topic config and consumer harness. Lane kafka. KIT-functional: yes.

## Notes

- **Assumptions:** Slack approvals granted; Kafka topics and Postgres instances available in-cluster; reminders rely on Kafka timers rather than external cron.
- **Risks:** Slack latency spikes (mitigated via async ack), fairness disputes (transparent summary messaging), reminder timing accuracy (monitor offsets).
- **Mitigations:** Feature flags for reminders, config bounds validated server-side, structured logging with correlation IDs for audits.
- **Lane Coverage:** Infra lane covers Kubernetes/Kong/Vault considerations referenced within python App work via shared utilities; ensure secrets fetched only through Vault stubs.

PLAN_END