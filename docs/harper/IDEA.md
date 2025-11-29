# IDEA — coffeebuddy

## Vision
CoffeeBuddy streamlines office coffee runs entirely within the corporate network: teammates submit orders via Slack, one teammate is fairly assigned as runner, reminders are sent, and preferences are remembered—without relying on public cloud. Within two weeks, deliver an on-prem Slack bot that runs a full coffee round end-to-end for a pilot team of up to 30 users. The experience must feel “one-command simple”: start, collect, confirm, and notify in under 2 minutes. Differentiation comes from strict on-prem operation, alignment with existing enterprise stack (Kubernetes, Ory, Kong, Kafka, Vault), and fairness logic that is transparent to users.

## Problem Statement
Office teams coordinate coffee runs with ad-hoc Slack threads. Messages get buried, orders are incomplete, and the same people are repeatedly “volunteered,” causing frustration. In regulated or high-security environments, off-the-shelf SaaS bots are blocked, and homegrown scripts lack audibility and reliability. Today, a single run can consume 5–10 minutes of back-and-forth messages and still result in incorrect or missing orders, especially for teammates with specific preferences. For slice-1, the problem is considered solved when a pilot Slack channel can: trigger a coffee run with one command, collect orders via structured interactive messages, automatically assign a runner using a simple fairness rule, and post a summarized order list plus DM notifications—all running on-prem and observable.

## Target Users & Context
- **Primary user:** office teammates using Slack who:
  - Need to quickly place coffee orders without manual message scrolling.
  - Occasionally act as the runner and need a clear, consolidated list.
  - Want their usual drink remembered to avoid retyping.
- **Secondary stakeholders:**
  - Office managers wanting visible fairness and reduced coordination time.
  - IT/Platform teams needing an on-prem, compliant Slack integration.
- **Operating context:**
  - Enterprise Slack workspace (slash commands, interactive messages).
  - On-prem Kubernetes cluster, internal gateways only.
  - Typical pilot volume: 1–10 runs/day, 5–30 participants/run.
  - English-only for slice-1 (Assumption).

## Value & Outcomes (with initial targets)
- Outcome 1: Reduce coordination time per coffee run from ~5–10 minutes to ≤2 minutes for 80% of runs (Assumption).
- Outcome 2: Achieve ≥90% order accuracy (no missing or wrong items) for runs managed via CoffeeBuddy.
- Outcome 3: Ensure fair runner rotation so no individual runs >20% of runs over a 4-week period in a channel (Assumption).
- Outcome 4: Reach ≥60% of active channel members participating in at least one CoffeeBuddy run per week in the pilot.
- Outcome 5: Achieve ≥4.2/5 average satisfaction score from pilot users on ease of use and clarity of summaries.

## Out of Scope (slice-1)
- Payment handling, tipping, or integration with POS/payment systems.
- Delivery logistics, route optimization, or integration with external vendors (e.g., Starbucks APIs).
- Mobile apps or channels beyond Slack (no email, MS Teams, web UI for slice-1).
- Multi-language UX beyond English and advanced preference logic (e.g., dietary rules).
- Complex analytics dashboards; only minimal usage metrics/logs for slice-1.
- Cross-workspace or cross-tenant operation; single enterprise Slack workspace only.

## Technology Constraints (SPEC-ready)
```yaml
tech_constraints:
  version: 1.0.0
  profiles:
    - name: app-core
      runtime: python@3.12
      platform: kubernetes
      api:
        - rest
        - slack.events
      storage:
        - postgres
      messaging:
        - kafka
      auth:
        - oidc
      observability:
        - prometheus
    - name: ai-rag
      runtime: python@3.12
      platform: kubernetes
      api:
        - internal.rag
      storage:
        - qdrant
      messaging: []
      auth:
        - service-token
      observability:
        - opentelemetry
  capabilities:
    - type: ai.generation
      mode: chat
      params:
        max_tokens: 9500
    - type: ai.rag.index
      formats:
        docx: true
        pdf: true
        xlsx: true
        pptx: true
    - type: ci.quality
      coverage_min: 80
```

## Risks & Assumptions

* **Business assumptions:**
  - Slack Enterprise is approved for internal use; incoming/outgoing webhooks allowed via internal gateway.  
  - Pilot team (1–2 channels, ~30 users) is committed to daily use during testing.
  - No additional approvals needed beyond standard internal app registration (Assumption).
* **Technical assumptions:**
  - Existing on-prem stack: Kubernetes, Postgres, Kafka, Kong Gateway, Ory, Vault, Prometheus already available and managed.
  - Slack app credentials and signing secrets can be securely stored in Vault.
  - Slack rate limits are manageable at expected volumes; Kafka buffers event bursts.
* **Delivery risks:**
  - Delays in Slack app approval or gateway routing configuration.
  - Conflicting corporate policies on interactive apps or bots in Slack.
  - Limited DevOps capacity for CI/CD and observability integration.
* **UX risks:**
  - Low adoption if commands/flows are not discoverable or feel “heavy.”
  - Confusion around fairness logic if not clearly communicated.
  - Over-notification causing users to mute the bot/channel.

## Success Metrics (early slice)

* **TTFA (Time-to-First-Action):** ≤5 minutes from initial bot installation in a channel to successfully completing the first coffee run.
* **Task success (slice flows):** ≥80% of users can start and complete a coffee run (start → orders collected → runner assigned → summary posted) without external help.
* **Critical error rate:** ≤2% of runs fail due to system issues (timeouts, crashes, missing summaries).
* **Idea→Demo lead time:** ≤10 calendar days from this IDEA to a working demo in a non-production Slack workspace.
* **CSAT/NPS (pilot):** ≥4.2/5 average rating on a simple in-Slack feedback prompt after runs.

## Sources & Inspiration

* Internal notes: Original CoffeeBuddy IDEA.clike.md describing on-prem Slack-based coffee coordination.
* Market scan / baseline: General patterns from Slack platform usage (slash commands, interactive messages) and internal standards for Kubernetes, Ory Hydra/Kratos, Kong Gateway, Vault, Kafka (Assumption; no external docs attached).

## Non-Goals

* Replacing broader office resource management or task assignment tools.
* Providing a full-featured ordering platform for external cafes or vendors.
* Handling legal/non-repudiation workflows or e-signatures.
* Achieving internet-scale multi-tenant SaaS performance before validating value.
* Deep AI personalization or recommendation systems for drink choices in slice-1.

## Constraints

* **Budget:** Limited to existing internal platform resources and one squad’s part-time effort for a 2–3 week pilot (Assumption).
* **Timeline:** Slice-1 pilot-ready bot within 2 weeks; live pilot within 4 weeks (Assumption).
* **Compliance:** Must comply with internal security and data-handling standards; user IDs and preferences treated as internal PII; logs must avoid storing message bodies unnecessarily.
* **Legal:** No storage of sensitive personal data beyond names/user IDs and drink preferences; retention aligned with internal policies (e.g., 90-day logs, Assumption).
* **Platform limits:** Must respect Slack API quotas; all traffic via internal gateway; dev and prod workspaces separated; clear SLAs not required for slice-1 but target ≥99% availability during business hours.

## Strategic Fit

* Supports collaboration and employee-experience OKRs by reducing friction in daily rituals and demonstrating fast, safe Slack automation on-prem.
* Serves as a reference pattern for future internal Slack bots leveraging Kubernetes, Ory, Kong, Kafka, and Vault.
* Executive sponsors: local office leadership and Platform/DevEx owners (Assumption); go/no-go after pilot CSAT and usage review.
* Cross-function impacts: IT Security (Slack app review, scopes), DPO/Privacy (preference data), Platform/Infra (Kubernetes, DB, Kafka, monitoring), and potentially HR/Facilities for broader rollout.

## /spec Handoff Readiness (bridge section)

* **Functional anchors:**
  - Capability 1: Start a coffee run in a Slack channel via slash command (e.g., `/coffee`) and basic parameters (e.g., pickup time).
  - Capability 2: Collect structured coffee orders from channel members using interactive Slack messages/blocks.
  - Capability 3: Persist user coffee preferences and offer “use last order” as a quick option.
  - Capability 4: Automatically assign a runner using a simple fairness algorithm based on past runs in that channel.
  - Capability 5: Generate and post a consolidated order summary in-channel and DM it to the runner.
  - Capability 6: Send time-based reminders to participants and runner (e.g., before pickup).
  - Capability 7: Provide minimal admin/config commands (e.g., enable/disable in channel, reset data for channel).
  - Capability 8: Emit basic metrics and logs for runs (count, duration, errors) for Prometheus consumption.

* **Non-functional anchors:**
  - P95 latency ≤2 seconds for command responses and interactive actions under expected load.
  - Availability target: ≥99% during local business hours for pilot; graceful degradation with clear error messages.
  - Security: OIDC-based service auth in-cluster, Slack signing secret verification, least-privilege Slack scopes, encrypted secrets via Vault.
  - Observability: Structured logs with correlation IDs, basic Prometheus metrics (requests, errors, run counts, latency), and optional traces for key flows.
  - Data lifecycle: Store only necessary user IDs, display names, and drink preferences; channel-configurable data retention (default 90 days, Assumption); safe deletion endpoints for channel resets.

* **Acceptance hooks:**
  - Capability 1:
    - Given the app is installed in a channel, when a user types `/coffee`, then a confirmation/intro message appears within 2 seconds.
    - When the command is invoked with invalid parameters, then the bot responds with a clear error and usage hint.
  - Capability 2:
    - When a run is started, then all channel members see an interactive order prompt where they can submit or edit their order.
    - When at least one order is submitted, then the run status reflects the current count of participants.
  - Capability 3:
    - When a user completes an order, then their preference is stored and re-offered on the next run.
    - When a stored preference exists, then the user can confirm their prior order with a single click.
  - Capability 4:
    - When a run is closed, then a runner is selected based on the lowest recent run count in that channel.
    - When the same user is currently at the top of the fairness list, then they are not selected if they ran the last run (unless they opt in).
  - Capability 5:
    - When the run is closed, then a single summary message is posted listing all participants and their orders.
    - When the summary is generated, then the selected runner receives a DM with the same list and any notes.
  - Capability 6:
    - When a run is scheduled with a pickup time, then a reminder is sent to the runner X minutes before that time (configurable, default 5).
    - When reminders are disabled for a channel, then no reminder messages are sent.
  - Capability 7:
    - When an admin user invokes an admin command (e.g., `/coffee admin`), then they can view and adjust basic settings for that channel.
    - When data reset is confirmed, then historical run data and preferences for that channel are removed and no longer influence fairness.
  - Capability 8:
    - When the system is running, then Prometheus can scrape metrics including total_runs, failed_runs, and run_duration_seconds.
    - When an internal error occurs, then a structured log entry with correlation ID and error details is recorded without exposing secrets.