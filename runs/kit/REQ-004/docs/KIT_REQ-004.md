# KIT — REQ-004 (Reminder scheduling and delivery)

## Scope
Implements reminder scheduling and dispatch primitives:
- Deterministic Kafka payload generation for runner and last-call reminders.
- Async worker that respects tolerance windows and exports metrics.
- Slack-focused reminder sender consuming the existing Slack helper surface.
- Extensive unit coverage for scheduler, worker, and sender seams.

## Highlights
- **Composition-first:** scheduler emits plain `KafkaEvent`s; worker consumes `ReminderPayload`; Slack sender implements the shared `ReminderSender` Protocol for downstream wiring.
- **Fault containment:** channel/runner state validation up-front skips useless work, while failures bubble up for Kafka retry after metrics/logs are captured.
- **Deterministic timing:** scheduler normalizes timestamps to UTC and enforces future scheduling; worker waits until reminders fall within the configured tolerance window.
- **Slack integration seam:** `SlackReminderSender` accepts the messenger from `coffeebuddy.api.slack_runs` and a resolver to look up Slack IDs, allowing reuse across service boundaries.

## Tests
`pytest -q runs/kit/REQ-004/test`

Covers:
- Reminder scheduling for runner + last-call permutations and minimum-future adjustments.
- Worker tolerance waiting, skip scenarios, and metrics emission.
- Slack sender success & failure paths.

## Follow-ups
- Wire `ReminderScheduler` invocation into the run close workflow (REQ-003 surface).
- Bind `ReminderWorker` to the Kafka consumer configured in REQ-007.
- Extend resolver implementation to leverage existing repositories for Slack ID lookups.