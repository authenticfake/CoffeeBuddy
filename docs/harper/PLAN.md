# PLAN — coffeebuddy

## Plan Snapshot

- **Counts:** total=10 / open=6 / in_progress=4 / done=0 / deferred=0
- **Progress:** 0% complete
- **Checklist:**
  - [x] SPEC aligned
  - [x] Prior REQ reconciled
  - [x] Dependencies mapped
  - [x] KIT-readiness per REQ confirmed

## Tracks & Scope Boundaries

- **Tracks:**
  - App:
    - Slack-facing CoffeeBuddy service, run lifecycle, orders and preferences
    - Fairness algorithm and runner assignment
    - Reminder scheduling logic
    - Admin and configuration flows
    - Metrics, logging, and error UX
  - Infra:
    - Database schema and migrations for CoffeeBuddy
    - Kafka topics and consumer/producer wiring
    - Kubernetes, Kong, Vault, Ory, Prometheus integration

- **Out of scope / Deferred:**
  - Any non-Slack interfaces or UIs
  - Advanced analytics or external BI integrations
  - Multi-tenant or multi-workspace scaling features
  - Payment, tipping, or vendor integrations
  - AI-based personalization

## Module/Package & Namespace Plan (per KIT)

Canonical Python package root: `coffeebuddy`. All App REQs extend this tree, not invent new top-level roots.

Suggested layering:

- `coffeebuddy.api.slack` — HTTP handlers for Slack commands and interactions
- `coffeebuddy.domain.runs` — run aggregate, lifecycle logic
- `coffeebuddy.domain.orders` — order and preference logic
- `coffeebuddy.domain.fairness` — runner assignment algorithms
- `coffeebuddy.domain.reminders` — reminder scheduling computations
- `coffeebuddy.domain.admin` — admin commands and configuration domain logic
- `coffeebuddy.infrastructure.db` — DB session, repositories, migrations glue
- `coffeebuddy.infrastructure.kafka` — Kafka producers and consumers
- `coffeebuddy.infrastructure.slack_client` — typed wrapper around Slack Web API
- `coffeebuddy.infrastructure.secrets` — Vault integration, config loading
- `coffeebuddy.infrastructure.auth` — Ory and OIDC helpers
- `coffeebuddy.observability` — logging, metrics, tracing helpers
- `coffeebuddy.app` — application wiring, dependency injection, startup

Per-REQ ownership:

- REQ-001:
  - Primary: `coffeebuddy.api.slack`
  - Shared: `coffeebuddy.infrastructure.slack_client`, `coffeebuddy.observability`
  - May create new modules under `coffeebuddy.api` only

- REQ-002:
  - Primary: `coffeebuddy.domain.runs`
  - Shared: `coffeebuddy.infrastructure.db`
  - Can extend `coffeebuddy.domain.runs`, must reuse DB infra

- REQ-003:
  - Primary: `coffeebuddy.domain.orders`
  - Shared: `coffeebuddy.domain.runs`, `coffeebuddy.infrastructure.db`, `coffeebuddy.api.slack`
  - Can extend `coffeebuddy.domain.orders` and Slack views only

- REQ-004:
  - Primary: `coffeebuddy.domain.fairness`
  - Shared: `coffeebuddy.domain.runs`, `coffeebuddy.domain.orders`, `coffeebuddy.infrastructure.db`
  - Must not duplicate run or stats models

- REQ-005:
  - Primary: `coffeebuddy.domain.reminders`
  - Shared: `coffeebuddy.infrastructure.kafka`, `coffeebuddy.domain.runs`
  - May add consumer logic under `coffeebuddy.app` but reuse Kafka module

- REQ-006:
  - Primary: `coffeebuddy.domain.admin`
  - Shared: `coffeebuddy.infrastructure.db`, `coffeebuddy.api.slack`, `coffeebuddy.observability`
  - Must extend `domain.admin` and Slack admin handlers only

- REQ-007:
  - Primary: `coffeebuddy.observability`
  - Shared: used by all modules
  - Extends existing logging and metrics utilities only, no business logic

- REQ-008:
  - Primary: `coffeebuddy.infrastructure.db`
  - Shared: all domain modules
  - Creates migration structure, connection management, no business rules

- REQ-009:
  - Primary: `coffeebuddy.infrastructure.kafka`
  - Shared: reminders, analytics, run lifecycle
  - Creates topic config bindings and producer/consumer wrappers only

- REQ-010:
  - Primary: `coffeebuddy.infrastructure.runtime`
  - Shared: `coffeebuddy.app`, `coffeebuddy.infrastructure.secrets`, `coffeebuddy.infrastructure.auth`
  - Kubernetes, Kong, Vault, Ory, Prometheus glue, no domain logic

## REQ-IDs Table

| ID | Title | Acceptance | DependsOn | Track | Status |
|---|---|---|---|---|---|
| REQ-001 | Slack slash command and interaction HTTP endpoints | Handle Slack slash command POST with signature verification and latency within target<br/>Handle Slack interactive callbacks updating messages and state appropriately<br/>Return clear guidance on invalid command syntax without exposing internal details<br/>Include correlation IDs on all request logs and responses where applicable<br/>Avoid logging Slack tokens signing secrets or full payload bodies | REQ-007, REQ-010 | App | open |
| REQ-002 | Run lifecycle domain model and persistence | Define User Channel Run models matching SPEC logical schema<br/>Persist Run records with correct status timestamps and relationships<br/>Associate new runs with appropriate User and Channel records<br/>Provide repository queries for latest runs per channel and status<br/>Emit run_created domain events ready for Kafka publishing | REQ-008 | App | open |
| REQ-003 | Order collection and preference persistence UX | Allow users to create edit and cancel orders for an open run<br/>Enforce one active order per user per run in persistence layer<br/>Persist UserPreference records storing last confirmed order per channel<br/>Update channel message participant counts accurately after changes<br/>Emit order_updated events suitable for Kafka without sensitive text | REQ-001, REQ-002, REQ-007 | App | open |
| REQ-004 | Fair runner assignment algorithm and transparency | Maintain RunnerStats per user per channel with counts and timestamps<br/>Implement fairness algorithm using configurable recent window parameters<br/>Exclude last runner unless opted in according to rules<br/>Integrate algorithm into run closing updating Run and RunnerStats<br/>Provide human readable explanation of runner choice in summary | REQ-002, REQ-003, REQ-008 | App | open |
| REQ-005 | Reminder scheduling and Kafka driven execution | Schedule reminders when runs have pickup_time and reminders enabled<br/>Represent reminders as durable Kafka events with due timestamps<br/>Consume reminder events and send Slack DMs and last call messages<br/>Respect per channel reminder enable disable settings at execution<br/>Ensure reminder timing within plus minus one minute of target | REQ-002, REQ-007, REQ-009 | App | open |
| REQ-006 | Admin configuration commands and channel data reset | Expose /coffee admin command with admin only interactive UI<br/>Validate admin rights using Slack roles or configured lists<br/>Persist channel settings and retain audit trail for changes<br/>Implement channel scoped data reset honoring retention rules<br/>Communicate results of admin actions clearly in Slack messages | REQ-001, REQ-002, REQ-003, REQ-008 | App | open |
| REQ-007 | Metrics logging and error handling behavior | Provide Prometheus metrics endpoint with required counters and histograms<br/>Implement structured JSON logging including correlation IDs and categories<br/>Define error handling middleware for HTTP endpoints and background tasks<br/>Avoid logging secrets or unnecessary message contents in all paths<br/>Validate metrics and logs against pilot observability expectations | REQ-010 | App | in_progress |
| REQ-008 | Postgres schema migrations and repository layer | Design SQL schema for all CoffeeBuddy entities with constraints<br/>Implement idempotent migrations usable across dev test and prod<br/>Provide connection pooling and health checks for Postgres access<br/>Implement repositories supporting domain operations efficiently<br/>Document schema and migration procedures for platform teams | REQ-010 | Infra | in_progress |
| REQ-009 | Kafka topics configuration and client wrappers | Define and document required Kafka topics and configurations<br/>Implement producer wrapper for publishing domain events safely<br/>Implement consumer abstraction with offset and error handling<br/>Expose metrics for Kafka publish failures lag and processing<br/>Validate event flows in test environment end to end | REQ-010 | Infra | in_progress |
| REQ-010 | Runtime integration with Kubernetes Kong Vault Ory Prometheus | Build Python 3.12 container image with health endpoints exposed<br/>Provide Kubernetes manifests including Deployment Service and config<br/>Configure Kong Vault Ory and Prometheus integration for service<br/>Ensure deployment uses only on prem resources and Slack<br/>Document deployment steps configuration and environment variables |  | Infra | in_progress |

zed users<br>Channel config updates persisted and auditable<br>Data reset removes channel historical impact on fairness|REQ-001, REQ-002, REQ-003, REQ-008|App|open|
|REQ-007|Metrics logging and error handling behavior|Prometheus metrics endpoint exposes required counters and histograms<br>Structured logs include correlation IDs and avoid sensitive data<br>User facing errors are clear and instructive|REQ-010|App|open|
|REQ-008|Postgres schema migrations and repository layer|All entities mapped to tables with constraints<br>Migrations runnable idempotently across environments<br>Repository APIs support domain operations efficiently|REQ-010|Infra|open|
|REQ-009|Kafka topics configuration and client wrappers|Required topics created and documented<br>Producer and consumer wrappers abstract Kafka usage<br>Error handling and retries configured per policy|REQ-010|Infra|open|
|REQ-010|Runtime integration with Kubernetes Kong Vault Ory Prometheus|Service runs on Kubernetes with health endpoints<br>Kong route exposes Slack endpoints securely<br>Vault Ory Prometheus wired per constraints| |Infra|open|

### Acceptance — REQ-001

- Implement HTTP endpoint to receive Slack slash commands routed via Kong using POST and Slack signature verification.
- Implement HTTP endpoint for Slack interactive payloads handling block actions and modal submissions with signature verification.
- Respond to valid `/coffee` commands within 2 seconds with an ephemeral or public interactive message starting a run.
- Return clear usage guidance when command syntax is invalid including correct examples without exposing internal details.
- Ensure endpoints validate Slack workspace configuration and return actionable error messages when scopes or setup are missing.
- Correlate each incoming Slack request with a generated correlation ID and propagate it through logs and downstream calls.
- Ensure endpoints never log raw Slack tokens signing secrets or full message bodies beyond minimal debugging fields.

### Acceptance — REQ-002

- Define domain models for User Channel Run and link them according to the SPEC logical data model.
- Persist Run records with statuses open closed canceled failed including timestamps for started and closed times.
- Ensure run creation associates the Slack channel and initiator user creating Channel and User rows when missing.
- Provide repository methods to query latest runs per channel and by status to support workflows and fairness logic.
- Enforce invariants so a run cannot transition from closed to open or from failed to closed via repository APIs.
- Emit a domain event object representing run_created to be published to Kafka without coupling to Kafka implementation.
- Handle transactional persistence so run creation and event enqueueing either both succeed or inconsistencies are avoided.

### Acceptance — REQ-003

- Implement Slack interactive flows allowing users to create edit and cancel orders tied to a specific open run.
- Enforce one active non canceled order per user per run rejecting or updating duplicates according to UX design.
- Persist Order and UserPreference entities storing last confirmed order text per user per channel.
- Update preferences when users confirm or reuse orders ensuring last_used_at reflects latest application.
- Update the channel run message with accurate participant counts reflecting non canceled orders only.
- Support a one click use last order action when a stored preference exists returning a helpful message when it does not.
- Publish order_updated domain events for Kafka including run user and change type without sensitive free text bodies.

### Acceptance — REQ-004

- Implement RunnerStats model tracking runs_served_count and last_run_at per user per channel.
- Implement fairness algorithm selecting runner with minimal runs_served_count within configurable window and tie breaking by last_run_at.
- Exclude ineligible users based on rules including previous immediate runner when they have not opted in to run again.
- Integrate algorithm into run closing flow updating Run.runner_user_id and RunnerStats transactionally.
- Ensure algorithm options such as fairness_window_runs and inclusion rules are configurable per channel within global bounds.
- Post a concise explanation in the run summary describing why the runner was selected referencing fairness rules.
- Provide deterministic behavior for identical inputs and log decisions with correlation IDs without exposing sensitive user data.

### Acceptance — REQ-005

- When a run is created with pickup_time schedule reminder jobs according to channel reminder_offset_minutes configuration.
- Represent scheduled reminders as Kafka events or durable jobs including run identifier due time and reminder type.
- Implement Kafka consumer or scheduler that sends DM reminders to runner and optional last call messages at due times.
- Ensure reminders respect per channel enable disable flags and do not fire when reminders are turned off before due time.
- Handle drift so runner reminders are delivered within plus or minus one minute of target time under normal load.
- Guarantee idempotency so duplicate reminder events do not produce duplicate Slack messages to users.
- Emit reminder_sent events and metrics to support monitoring of reminder success and failures.

### Acceptance — REQ-006

- Implement `/coffee admin` command and interactive admin UI accessible only to authorized channel admins or owners.
- Validate admin authorization using Slack roles or configured admin user IDs returning clear denial messages when unauthorized.
- Allow admins to configure channel level settings including enable disable reminder offsets fairness window and retention.
- Persist Channel configuration changes and write ChannelAdminAction audit records describing action type details admin and timestamp.
- Implement channel data reset that removes or anonymizes Run Order UserPreference and RunnerStats records for that channel.
- Ensure data reset operations do not affect other channels and do not break schema or future operations.
- Provide confirmation and summary messages in Slack after each admin action describing what changed and any impact.

### Acceptance — REQ-007

- Expose Prometheus metrics endpoint including counters for runs started completed failed and request types from Slack.
- Implement histograms for run duration and response latency for slash commands and interactive actions supporting P95 calculations.
- Implement structured JSON logging including correlation IDs run IDs channel IDs and error categories but not secrets or full texts.
- Provide consistent error handling middleware translating internal exceptions into user safe Slack messages with recovery guidance.
- Record metrics and logs for error types enabling calculation of critical error rates and detection of degraded dependencies.
- Ensure metrics endpoint protected appropriately but accessible to Prometheus according to on prem network standards.
- Validate logs and metrics in a test environment to confirm they satisfy pilot observability requirements.

### Acceptance — REQ-008

- Design SQL schema for all entities in SPEC including keys indexes foreign keys and enumerated statuses.
- Implement migration scripts compatible with chosen migration tool enabling repeatable idempotent migrations across environments.
- Provide database access layer creating pooled connections using credentials from Vault with health checks for readiness probes.
- Implement repository interfaces for User Channel Run Order UserPreference RunnerStats ChannelAdminAction with CRUD methods.
- Enforce referential integrity via foreign keys and application checks ensuring deletions or resets maintain consistency.
- Add minimal performance indexes to support expected query patterns including recent runs per channel and stats lookups.
- Document schema and migration usage for platform teams including rollback strategy for early pilot issues.

### Acceptance — REQ-009

- Define Kafka topics for coffeebuddy.run.events and coffeebuddy.reminder.events with appropriate partitions and retention settings.
- Implement producer wrapper providing type safe publishing for domain events with standardized keys headers and error handling.
- Implement consumer abstraction supporting subscription to reminder and run events with offset management and graceful shutdown.
- Configure retry and dead letter handling strategy for failed event processing aligned with enterprise Kafka practices.
- Ensure producers and consumers expose metrics for publish failures lag and processing errors for observability.
- Provide configuration for topic names brokers and security using environment variables or config files loaded via Vault.
- Validate local and test environment operation with mock or shared Kafka cluster demonstrating end to end event flows.

### Acceptance — REQ-010

- Package CoffeeBuddy as a Python 3.12 container with health endpoints readiness and liveness implemented.
- Provide Kubernetes manifests or Helm templates for Deployment Service ConfigMap and secrets integration with Vault.
- Configure Kong route to expose Slack endpoints over HTTPS with Slack IP restrictions and request size limits as needed.
- Integrate Ory OIDC for any internal calls made by CoffeeBuddy following organization patterns and token handling rules.
- Expose Prometheus scrape configuration for the service using standard annotations or ServiceMonitor resources.
- Document deployment steps including environment variables required DNS and routing assumptions and Slack app configuration.
- Validate that no public cloud dependencies are introduced and all connectivity is via on prem components and Slack.

## Dependency Graph

- REQ-001 -> REQ-007, REQ-010
- REQ-002 -> REQ-008
- REQ-003 -> REQ-001, REQ-002, REQ-007
- REQ-004 -> REQ-002, REQ-003, REQ-008
- REQ-005 -> REQ-002, REQ-007, REQ-009
- REQ-006 -> REQ-001, REQ-002, REQ-003, REQ-008
- REQ-007 -> REQ-010
- REQ-008 -> REQ-010
- REQ-009 -> REQ-010
- REQ-010 -> (no dependencies)

## Iteration Strategy

- Batch 1 (foundations, Infra focus, size M):
  - REQ-010, REQ-008, REQ-009, REQ-007
  - Goal: running service skeleton on Kubernetes with DB, Kafka, metrics wired but minimal business logic.
- Batch 2 (core run lifecycle and Slack shell, size M):
  - REQ-001, REQ-002
  - Goal: start a run via Slack and persist basic run records with observability.
- Batch 3 (orders, preferences, fairness, size L):
  - REQ-003, REQ-004
  - Goal: full run lifecycle with orders and fair runner assignment including summary posts.
- Batch 4 (reminders and admin, size M):
  - REQ-005, REQ-006
  - Goal: configurable reminders and admin tooling including data reset and enable/disable.

Confidence: ±1 batch for completion depending on infra readiness and Slack approval timing.

## Test Strategy

- Per REQ:
  - Unit tests for domain logic in runs, orders, fairness, reminders, admin, observability helpers.
  - Unit tests for HTTP handlers using Slack payload fixtures and signature verification stubs.
  - Repository tests against a Postgres test instance or container validating schema and transactions.
  - Kafka integration tests using test topics or embedded cluster for producer and consumer wrappers.
- Per batch:
  - Batch 1: health checks, DB connectivity, Kafka connectivity, metrics exposure smoke tests.
  - Batch 2: end to end Slack command simulation from HTTP ingress to DB persistence.
  - Batch 3: E2E flows for start run, submit orders, close run, verify fairness and summaries.
  - Batch 4: E2E flows for reminders timing and admin configuration including data reset behavior.
- Cross cutting:
  - Performance tests for slash commands and interactions verifying P95 latency under pilot load.
  - Security checks for secrets handling, log redaction, and Slack signature verification.
  - Observability checks confirming metrics scraping and log structure.

## KIT Readiness (per REQ)

Common structure:

- Source root: `/runs/kit/<REQ-ID>/src`
- Test root: `/runs/kit/<REQ-ID>/test`
- Python package root inside src: `coffeebuddy`

For all REQs, KIT-functional: yes, assuming access to minimal scaffolding and allowed libraries within constraints.

- REQ-001:
  - Root module: `coffeebuddy.api.slack`
  - Files under `/runs/kit/REQ-001/src/coffeebuddy/api/slack`
  - Tests under `/runs/kit/REQ-001/test/api/slack`
  - Expects mock Slack request payloads and signature verification helpers.
  - No external network calls in tests; Slack client mocked.

- REQ-002:
  - Root module: `coffeebuddy.domain.runs`
  - Files under `/runs/kit/REQ-002/src/coffeebuddy/domain`
  - Tests under `/runs/kit/REQ-002/test/domain`
  - Uses in memory or test Postgres via `coffeebuddy.infrastructure.db` contracts.

- REQ-003:
  - Root module: `coffeebuddy.domain.orders`
  - Files under `/runs/kit/REQ-003/src/coffeebuddy/domain`
  - Tests under `/runs/kit/REQ-003/test/domain`
  - Reuses run models from REQ-002; imports not duplicated.

- REQ-004:
  - Root module: `coffeebuddy.domain.fairness`
  - Files under `/runs/kit/REQ-004/src/coffeebuddy/domain`
  - Tests under `/runs/kit/REQ-004/test/domain`
  - Deterministic algorithm tests with controlled histories and configurations.

- REQ-005:
  - Root module: `coffeebuddy.domain.reminders`
  - Files under `/runs/kit/REQ-005/src/coffeebuddy/domain`
  - Tests under `/runs/kit/REQ-005/test/domain`
  - Kafka interfaces mocked; time control via injected clock.
  - Optional API documentation collection for Slack reminder endpoints under `/runs/kit/REQ-005/test/api`.

- REQ-006:
  - Root module: `coffeebuddy.domain.admin`
  - Files under `/runs/kit/REQ-006/src/coffeebuddy/domain`
  - Tests under `/runs/kit/REQ-006/test/domain`
  - Slack admin flows tested with fixtures and DB reset operations on isolated schemas.

- REQ-007:
  - Root module: `coffeebuddy.observability`
  - Files under `/runs/kit/REQ-007/src/coffeebuddy`
  - Tests under `/runs/kit/REQ-007/test/observability`
  - Metrics and logging tested using in process collectors and log capture.

- REQ-008:
  - Root module: `coffeebuddy.infrastructure.db`
  - Files under `/runs/kit/REQ-008/src/coffeebuddy/infrastructure`
  - Tests under `/runs/kit/REQ-008/test/infrastructure`
  - Migrations executed in test containers; schema validation tests.

- REQ-009:
  - Root module: `coffeebuddy.infrastructure.kafka`
  - Files under `/runs/kit/REQ-009/src/coffeebuddy/infrastructure`
  - Tests under `/runs/kit/REQ-009/test/infrastructure`
  - Kafka clients mocked or pointed to ephemeral local cluster.

- REQ-010:
  - Root module: `coffeebuddy.infrastructure.runtime`
  - Files under `/runs/kit/REQ-010/src/coffeebuddy/infrastructure`
  - Tests under `/runs/kit/REQ-010/test/infrastructure`
  - Kubernetes manifests and configuration validated via schema or template tests rather than cluster deployment.

## Notes

- Lanes detected from TECH_CONSTRAINTS:
  - python (runtime: python@3.12, Kubernetes)
  - sql (storage: postgres)
  - kafka (messaging: kafka)
  - infra (Kubernetes, Kong, Vault, Ory, Prometheus inferred from SPEC)
- All REQs kept minimal and composable, targeting approximately a single focused implementation session each.
- CI coverage target aligned with constraints: ≥80% unit test coverage for new code paths is expected per REQ.
- No public cloud dependencies may be introduced; all infra integrations must assume on prem managed services.
- Slack workspace and app approval are assumed but should be validated early; otherwise, plan execution may be blocked.

PLAN_END