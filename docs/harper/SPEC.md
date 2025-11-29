# SPEC — coffeebuddy

## Summary
CoffeeBuddy is an on-prem Slack bot that coordinates office coffee runs end-to-end within a single enterprise Slack workspace. Users start a run with one slash command, submit or reuse coffee orders through interactive messages, a fair runner is automatically assigned, and a consolidated summary plus notifications are sent. The bot runs entirely in the corporate network on Kubernetes, using Postgres for state, Kafka for events, Kong for ingress, Ory for service auth, Vault for secrets, and Prometheus for observability.

## Goals
- Enable a pilot Slack channel (up to 30 users) to complete full coffee runs with CoffeeBuddy: start, collect orders, assign runner, summarize, and notify.
- Achieve a “one-command simple” UX: typical runs complete core bot interactions (start → orders collected → runner assigned → summary posted) in under 2 minutes.
- Implement a transparent fairness algorithm for runner assignment based on historical runs within a channel.
- Operate entirely on-prem within the enterprise Kubernetes environment and internal gateways, with no public-cloud dependencies.
- Provide basic admin controls and minimal metrics suitable for slice-1 observability and operational readiness.

## Non-Goals
- Payment processing, tipping, or integration with POS or external vendor APIs.
- Supporting channels beyond Slack (e.g., MS Teams, email, mobile apps) for slice-1.
- Complex analytics dashboards; only basic metrics and logs are delivered.
- Sophisticated personalization or dietary/allergy logic beyond “remember my last order.”
- Multi-tenant or cross-workspace SaaS-level scalability and isolation.

## Users & Context
- **Primary users**
  - Regular Slack users in office channels who place coffee orders and occasionally act as runner.
- **Secondary stakeholders**
  - Office managers seeking visible fairness and reduced time spent coordinating runs.
  - IT/Platform/Security teams who require on-prem, compliant Slack app deployment.
- **Context**
  - Single enterprise Slack workspace with slash commands and interactive blocks.
  - CoffeeBuddy deployed to an internal Kubernetes cluster behind Kong Gateway.
  - Pilot scope: 1–2 channels, 1–10 runs/day, 5–30 participants per run.
  - English-only UX and documentation for slice-1.

## Functional Requirements
- **FR1: Start Coffee Run**
  - Support a slash command (e.g., `/coffee`) to initiate a coffee run in a channel.
  - Allow optional parameters (e.g., pickup time, location note).
  - Respond within 2 seconds with a confirmation and interactive run message.

- **FR2: Order Collection**
  - Present channel users with interactive messages/blocks to:
    - Submit a new coffee order (free-text or structured fields).
    - Reuse their last stored order with a single action.
    - Edit or cancel their order before the run is closed.
  - Track orders per user and per run; prevent duplicate active orders for the same user/run.

- **FR3: Preference Persistence**
  - Store each user’s most recent confirmed order per channel as their preference.
  - Offer “Use last order” / “Repeat my usual” as a quick action on new runs.
  - Update the stored preference when a user submits a new order.

- **FR4: Fair Runner Assignment**
  - Maintain per-channel history of past runs and assigned runners.
  - Implement fairness algorithm:
    - Prefer users with the lowest count of runs served in a configured window (e.g., last N runs or last X days).
    - Avoid assigning the same runner two runs in a row unless they explicitly opt in.
  - Provide transparency by posting a brief explanation in the summary (e.g., “Runner chosen based on lowest recent run count”).

- **FR5: Run Lifecycle & Summary**
  - Allow the initiator (or channel-configured admins) to close the run.
  - On closing:
    - Finalize participant list and orders.
    - Assign a runner as per fairness algorithm.
    - Generate a consolidated summary, including:
      - Run metadata (channel, pickup time, location note).
      - Runner identity.
      - List of participants and their orders.
    - Post summary in the originating channel.
    - Send a DM to the runner with the same summary plus any additional notes (e.g., total item count).

- **FR6: Reminders & Scheduling**
  - When a pickup time is supplied:
    - Schedule a reminder to the runner X minutes before pickup (default 5, configurable per channel).
  - Support optional reminder to participants prior to run closing (e.g., “last call”).
  - Provide a way to disable reminders per channel via admin configuration.

- **FR7: Admin & Configuration**
  - Provide an admin mode (e.g., `/coffee admin`) to:
    - Enable/disable CoffeeBuddy per channel.
    - Configure default reminder offsets, fairness window parameters, and data retention per channel (within global bounds).
    - Initiate a data reset for the channel (removes historical runs and preferences for that channel).
  - Restrict admin features to authorized users (e.g., channel owners/admins or configured list, enforced by Slack roles/user IDs).

- **FR8: Metrics & Logging**
  - Emit metrics for:
    - Total runs started, completed, and failed.
    - Average and distribution of time from run start to close.
    - Errors by type.
  - Log key events with correlation IDs (per run) and without storing unnecessary message bodies.

- **FR9: Error Handling & User Feedback**
  - Provide clear user-facing error messages when:
    - Slack requests fail or time out.
    - Required Slack scopes or configurations are missing.
    - Internal errors occur before completion (with a suggestion to retry or contact support).
  - Fail gracefully and avoid partial inconsistent state (e.g., ensure runs have a clear status: open, closed, failed/canceled).

## Non-Functional Requirements
- **Performance**
  - P95 latency ≤2 seconds for:
    - Slash command acknowledgements.
    - Interaction responses (e.g., button clicks, order submissions).
  - Capable of handling up to 10 runs/day with 30 participants/run without degradation.

- **Availability**
  - Target ≥99% availability during local business hours for the pilot.
  - Degrade gracefully (e.g., read-only or error responses) rather than hard failures when dependencies are unavailable.

- **Security & Privacy**
  - All communication with Slack APIs secured via HTTPS through internal gateway.
  - Slack signing secret verification for all incoming requests.
  - Least-privilege Slack scopes for slash commands, channel messages, and DMs.
  - Store only necessary data: Slack user IDs, display names, channel IDs, simple drink preferences, and run metadata.
  - Respect data retention settings; default 90-day retention for run and preference data (assumption).

- **Compliance & Auditability**
  - All secrets retrieved from Vault and never logged.
  - Logs must be structured and avoid storing message content beyond what is necessary for debugging and metrics.
  - Support basic audit trail for admin actions (e.g., channel enable/disable, data resets).

- **Operability & Observability**
  - Expose Prometheus metrics endpoint.
  - Utilize structured logging (JSON) and include correlation IDs.
  - Provide readiness and liveness probes for Kubernetes.

- **Technology**
  - Implemented as a Python 3.12 service running on Kubernetes.
  - Use Postgres for persistence and Kafka for asynchronous/event-driven workflows.
  - Use OIDC-based in-cluster service auth (via Ory ecosystem).
  - Integrate behind Kong Gateway for inbound Slack traffic.

## High-Level Architecture
- **Components**
  - CoffeeBuddy API service (Python 3.12) on Kubernetes.
  - Postgres database (shared or dedicated) for preferences, runs, and configuration.
  - Kafka topics for Slack event ingestion and internal events (run created, order updated, run closed, reminder due).
  - Kong Gateway route for Slack to CoffeeBuddy.
  - Ory for OIDC-based service-to-service authentication and authorization.
  - Vault for Slack app credentials and signing secrets.
  - Prometheus for metrics scraping.

```mermaid
flowchart LR
    Slack[Slack Workspace] -->|Slash Cmd & Interactions (HTTPS)| Kong[Kong Gateway]
    Kong -->|Verified Slack Requests| CoffeeBuddy[CoffeeBuddy Service (Python)]
    CoffeeBuddy -->|Read/Write| Postgres[(Postgres)]
    CoffeeBuddy -->|Produce/Consume Run Events| Kafka[(Kafka)]
    CoffeeBuddy -->|Fetch Secrets| Vault[(Vault)]
    CoffeeBuddy -->|Metrics| Prometheus[(Prometheus)]
    CoffeeBuddy -->|OIDC| Ory[Ory Auth]
    CoffeeBuddy -->|Messages & DMs| Slack
```

- **Key Flows**
  - Slack slash commands and interactive callbacks reach CoffeeBuddy via Kong.
  - CoffeeBuddy validates Slack signatures, processes requests, persists state, and sends Slack responses.
  - Long-running or scheduled actions (reminders, fairness calculations, cleanup) can be driven by Kafka events and internal schedulers.

## Interfaces
- **Slack Interfaces**
  - Slash command endpoint (e.g., `/coffee`):
    - Method: POST from Slack.
    - Content: standard Slack slash command payload (channel_id, user_id, text, trigger_id).
    - Response: immediate (ephemeral or public) message acknowledging run start and showing run controls.
  - Interactive component endpoint:
    - Method: POST from Slack for block actions and view submissions.
    - Content: Slack interaction payload (user actions on order forms, buttons).
    - Response: update of message blocks or ephemeral messages.

- **Internal HTTP API (CoffeeBuddy Service)**
  - Not necessarily user-facing; internal REST endpoints for:
    - Health: `/health/live`, `/health/ready`.
    - Metrics: `/metrics` (Prometheus format).
    - (Optional) Admin API for operations tasks if needed (e.g., forced cleanup).

- **Database Interface (Postgres)**
  - Accessed via an ORM or database client from the CoffeeBuddy service.
  - All DB credentials retrieved from Vault at startup or via sidecar.

- **Messaging Interface (Kafka)**
  - Topics:
    - `coffeebuddy.run.events` (run_created, run_updated, run_closed, run_failed).
    - `coffeebuddy.reminder.events` (reminder_scheduled, reminder_due, reminder_sent).
  - Used internally to decouple Slack interactions from reminders and analytics.

- **Auth & Secrets Interfaces**
  - OIDC tokens obtained by CoffeeBuddy service to access internal resources (if needed).
  - Vault K/V or dedicated secrets engine for Slack bot token, signing secret, and DB credentials.

## Data Model (logical)

### Entity: User
- id: UUID — PK
- slack_user_id: string — unique; maps to Slack user ID
- display_name: string — latest known Slack display name
- created_at: timestamp — record creation time
- updated_at: timestamp — last update time
- is_active: boolean — soft state, optional, default true

### Entity: Channel
- id: UUID — PK
- slack_channel_id: string — unique; Slack channel ID
- name: string — latest known Slack channel name
- enabled: boolean — whether CoffeeBuddy is enabled for this channel
- reminder_offset_minutes: integer — default reminder offset before pickup (e.g., 5)
- fairness_window_runs: integer — number of recent runs used for fairness calculation
- data_retention_days: integer — retention setting, default 90
- created_at: timestamp
- updated_at: timestamp

### Entity: Run
- id: UUID — PK
- channel_id: UUID — FK → Channel.id
- initiator_user_id: UUID — FK → User.id
- status: string — enum: [open, closed, canceled, failed]
- pickup_time: timestamp — optional; used for reminder scheduling
- pickup_note: string — optional free-text note (e.g., “Lobby cafe”)
- runner_user_id: UUID — FK → User.id; nullable until assigned
- started_at: timestamp — run creation time
- closed_at: timestamp — when run is closed
- failure_reason: string — optional; set when status = failed

### Entity: Order
- id: UUID — PK
- run_id: UUID — FK → Run.id
- user_id: UUID — FK → User.id
- order_text: string — user’s drink preference; short free-text or serialized fields
- is_final: boolean — true when user confirms order at run close
- created_at: timestamp
- updated_at: timestamp
- canceled_at: timestamp — optional; if user withdraws

### Entity: UserPreference
- id: UUID — PK
- user_id: UUID — FK → User.id
- channel_id: UUID — FK → Channel.id
- last_order_text: string — last confirmed order for this user in this channel
- last_used_at: timestamp — last time this preference was applied
- created_at: timestamp
- updated_at: timestamp

### Entity: RunnerStats
- id: UUID — PK
- user_id: UUID — FK → User.id
- channel_id: UUID — FK → Channel.id
- runs_served_count: integer — total runs served in configured fairness window
- last_run_at: timestamp — last time user was runner in this channel
- created_at: timestamp
- updated_at: timestamp

### Entity: ChannelAdminAction
- id: UUID — PK
- channel_id: UUID — FK → Channel.id
- admin_user_id: UUID — FK → User.id
- action_type: string — enum: [enable, disable, update_config, data_reset]
- action_details: json — configuration diffs or parameters
- created_at: timestamp

## Key Workflows

### Workflow: Start a Coffee Run
1. User types `/coffee [optional params]` in a Slack channel where the app is installed.
2. Slack sends slash command payload to Kong, which routes to CoffeeBuddy.
3. CoffeeBuddy verifies Slack signature and parses parameters (e.g., pickup time).
4. CoffeeBuddy creates a `Run` record with status `open`, linked to the `Channel` and `User`.
5. CoffeeBuddy posts an interactive message to the channel (summary of run, controls, order submission buttons).
6. Event `run_created` is published to Kafka.

### Workflow: Submit or Edit an Order
1. User clicks “Place order” or “Use last order” button in channel message.
2. Slack posts interaction payload to CoffeeBuddy.
3. CoffeeBuddy verifies signature and identifies the active `Run`.
4. If “Use last order”:
   - Fetches `UserPreference` for the user & channel.
   - Creates or updates `Order` linked to the run with `last_order_text`.
5. If “New order”:
   - CoffeeBuddy shows an interactive form/modal and stores the submitted text as an `Order`.
6. CoffeeBuddy updates the channel message to show the updated count of participants.
7. Event `order_updated` is published to Kafka.

### Workflow: Close Run and Assign Runner
1. Initiator or authorized admin uses a “Close run” button or slash subcommand.
2. CoffeeBuddy validates that the run is currently `open` and caller is authorized.
3. CoffeeBuddy:
   - Gathers all final `Order` records for the run.
   - Evaluates `RunnerStats` for the channel, excluding:
     - Users without orders in the run (if fairness only among participants).
     - The last runner if they served the immediately previous run and have not opted in.
   - Selects a runner based on minimum `runs_served_count`, then earliest `last_run_at`.
4. CoffeeBuddy updates `Run` with `runner_user_id`, sets status `closed`, sets `closed_at`.
5. CoffeeBuddy updates `RunnerStats` for the chosen runner.
6. CoffeeBuddy posts a summarized message in the channel and sends a DM to the runner with the same list.
7. Events `run_closed` and `runner_assigned` are published to Kafka.

### Workflow: Reminders
1. When a run is created with `pickup_time`, CoffeeBuddy schedules reminder jobs:
   - Runner reminder at `pickup_time - reminder_offset_minutes`.
2. Scheduler (internal or via Kafka events) triggers at reminder time:
   - Reads `Run` and channel config.
   - Sends DM reminder to the runner (and optional last-call message to channel if configured).
3. `reminder_sent` events are logged and emitted to Kafka.

### Workflow: Admin Configuration & Data Reset
1. Admin uses `/coffee admin` in a channel.
2. Slack sends payload to CoffeeBuddy; CoffeeBuddy verifies admin rights (e.g., Slack role or configured admin list).
3. CoffeeBuddy displays admin options: enable/disable, configure reminder offset, fairness window, retention, data reset.
4. Admin chooses an action; CoffeeBuddy:
   - Updates `Channel` configuration and logs a `ChannelAdminAction`.
   - For data reset, soft-deletes or hard-deletes all `Run`, `Order`, `UserPreference`, and `RunnerStats` for that channel (as per policy).
5. CoffeeBuddy confirms action to admin in Slack.

## Security & Compliance
- **Authentication & Authorization**
  - Slack → CoffeeBuddy: Slack signing secret verification for all incoming requests.
  - CoffeeBuddy → Slack: use bot token stored in Vault; scope-limited.
  - Internal services: in-cluster OIDC tokens for CoffeeBuddy when interacting with other internal components, managed via Ory.

- **Data Protection**
  - Secrets (Slack tokens, signing secrets, DB credentials) stored in Vault and injected at runtime (env/sidecar).
  - Transport encryption (TLS) enforced between Slack and Kong; internal TLS per org standards.
  - Data at rest encrypted per Postgres/storage policy (assumed handled by platform).

- **Privacy**
  - Store only Slack IDs, display names, run metadata, and drink preference texts; no sensitive personal data beyond that.
  - Configurable retention per channel, default 90 days; data reset functionality to support right-to-forget at channel level.
  - Logs and metrics must not contain raw Slack message bodies or order details beyond what is minimally necessary.

- **Auditability**
  - Track all admin actions (`ChannelAdminAction`) for enable/disable, config changes, and data resets.
  - Maintain timestamped run and runner assignment history for transparency and dispute resolution.

- **Compliance Alignment**
  - Operate fully on-prem with no external (public cloud) services beyond Slack itself.
  - Adhere to internal guidelines for Slack app scopes, logging, and PII handling.

## Deployment & Operations
- **Deployment**
  - Containerized CoffeeBuddy service deployed on Kubernetes.
  - Configured Kubernetes resources:
    - Deployment (with rolling updates).
    - Service (cluster-internal).
    - Ingress or Kong route for external Slack endpoints.
  - Environment configuration:
    - Slack credentials, DB URLs, JWT/OIDC configuration via Vault.
    - Channel defaults (retention, reminder offsets) via ConfigMap or environment variables.

- **Operations**
  - Health checks:
    - Liveness: basic service health (e.g., process up, main loop running).
    - Readiness: DB connectivity and Vault access.
  - Logging:
    - Structured logs with correlation IDs:
      - For each request/run, attach correlation ID through logs.
    - Log to centralized logging solution as per platform standards.
  - Monitoring:
    - Prometheus metrics endpoint (e.g., `/metrics`).
    - Default metrics:
      - `coffeebuddy_runs_total{status=...}`
      - `coffeebuddy_run_duration_seconds` (histogram)
      - `coffeebuddy_requests_total{type=slash|interaction}`
      - `coffeebuddy_errors_total{type=...}`
  - Alerting:
    - Configure base alerts on error rates and unavailability (e.g., readiness probe failures, high error ratios).

- **Environments**
  - At least two Slack workspaces/environments: dev/test and prod pilot.
  - Separate app credentials and configuration per environment.
  - CI/CD integration with quality gates (unit tests with ≥80% coverage per provided CI constraint).

## Risks & Mitigations
- **Risk: Slack app approval delays or gateway routing issues**
  - Mitigation: Use dev workspace early; coordinate with IT for Slack app review and Kong routing ahead of pilot.

- **Risk: Corporate policies restricting interactive bots**
  - Mitigation: Validate bot design with Security/Compliance early; minimize required scopes.

- **Risk: Fairness algorithm perceived as unfair or opaque**
  - Mitigation: Document and display simple, understandable fairness rules in a help/admin command; include short explanation in summary messages.

- **Risk: Over-notification causing user fatigue**
  - Mitigation: Provide channel-level configuration for reminders and default them to minimal necessary; ensure concise message formats.

- **Risk: Limited DevOps capacity**
  - Mitigation: Reuse existing platform templates for Python services, monitoring, and CI/CD; keep architecture minimal for slice-1.

- **Risk: Data handling concerns (preferences as PII)**
  - Mitigation: Implement channel-level retention and data reset; avoid unnecessary data fields and redact logs.

## Assumptions
- Slack Enterprise workspace is already approved and configured for internal use, with necessary app capabilities (slash commands, interactive components) enabled.
- On-prem Kubernetes, Postgres, Kafka, Kong, Ory, Vault, and Prometheus are available and managed by platform teams.
- Internal teams provide required DNS and routing so Slack can reach the CoffeeBuddy endpoints via Kong.
- No additional legal or compliance approvals beyond standard Slack app registration are required for the pilot.
- Only English language is required for slice-1 UX and documentation.
- Time-based scheduling can rely on platform-standard cron/scheduler or equivalent Kubernetes-native mechanism.

## Success Metrics
- TTFA (Time-to-First-Action): ≤5 minutes from bot installation in a channel to completion of first run.
- Task success: ≥80% of users can start and complete a coffee run without external help.
- Critical error rate: ≤2% of runs fail due to system issues (timeouts, crashes, missing summaries).
- Outcome time: For ≥80% of runs, core bot steps (start → orders collected → runner assigned → summary posted) complete in under 2 minutes (excluding human delays in placing orders).
- CSAT: ≥4.2/5 average rating from pilot users collected via a simple feedback prompt after runs.
- Fairness: Over any 4-week period in a pilot channel, no participant is assigned more than 20% of total runs (assuming sufficient eligible participants).

## Acceptance Criteria
- When the CoffeeBuddy app is installed in a pilot Slack channel and a user types `/coffee` with valid syntax, then within 2 seconds an interactive run message is posted acknowledging the run start and allowing order placement; invalid syntax yields a clear usage hint.
- When a run is open and at least 5 distinct users submit or reuse their orders via interactive components, then the channel message is updated to show an accurate count of participants, and each user’s last confirmed order is stored so that on the next run they can confirm it with a single click.
- When a run is closed via the “Close run” control, then a runner is selected according to the configured fairness rules (minimum recent runs served and not same as previous runner unless opted in), the `Run` is persisted with status `closed`, and a single summary message is posted in-channel plus a DM to the runner containing an identical order list.
- When a run is created with a pickup time 20 minutes in the future and the channel’s reminder offset is set to 5 minutes, then the designated runner receives a DM reminder no more than ±1 minute around 15 minutes from creation (5 minutes before pickup), and if reminders are disabled for the channel no such reminder is sent.
- Under pilot load (≤10 runs/day, ≤30 participants/run), 95% of slash command and interactive action responses complete in ≤2 seconds as observed in metrics, and Prometheus successfully scrapes metrics including total runs, failed runs, and run duration histograms without errors.
- When a channel admin issues `/coffee admin` and disables CoffeeBuddy for that channel, then any subsequent `/coffee` commands in that channel respond with a clear message stating that CoffeeBuddy is disabled and no runs or preferences are recorded; when the admin performs a data reset, existing run, order, preference, and runner stats for that channel are removed and no longer affect future fairness.
- For the duration of the pilot, logs and database records must not contain Slack OAuth tokens or signing secrets, and a sample audit of at least 10 runs confirms that admin actions (enable/disable, config change, reset) are recorded with timestamp, admin user ID, and action details.

## Out Of Scope
- Payment, tipping, or integration with vendors or POS systems.
- Non-Slack interfaces such as web UI, mobile apps, MS Teams, or email.
- Advanced analytics dashboards; any BI/visualization beyond basic metrics.
- Multi-language support, accessibility audits, or localization.
- Complex AI-based personalization or recommendation engines.

## Note from Harper Orchestrator (Super User) to be applied
- Keep the implementation minimal yet production-minded: favor clarity over cleverness, and build the fairness logic, reminder scheduling, and admin controls in a way that can be extended but does not over-engineer slice-1.
- Prioritize a smooth Slack UX and fast feedback: interactive flows must be intuitive, and error messages must instruct users how to recover.
- Maintain strict adherence to on-prem, internal-only architecture and platform standards (Kubernetes, Kong, Ory, Kafka, Vault, Postgres, Prometheus) as described; no additional external services should be introduced for slice-1.

```SPEC_END```