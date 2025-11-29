# REQ-004 — Reminder Scheduling and Delivery

## What’s Included
- **ReminderScheduler** (`coffeebuddy.jobs.reminders.scheduler`): accepts run + channel snapshots, builds `ReminderPayload`s, and publishes Kafka events via an injected publisher abstraction. Supports runner reminders and optional last-call alerts with per-channel config.
- **ReminderWorker** (`coffeebuddy.infra.kafka.reminder_worker`): consumes Kafka events, waits until the scheduled time within ±60s tolerance, invokes injected Slack senders, and records Prometheus metrics.
- **Tests** (`runs/kit/REQ-004/test/test_reminders.py`): cover scheduler behavior, disabled channels, worker timing, and skip paths.

## Usage
1. Instantiate `ReminderScheduler` with a publisher that knows how to write `KafkaEvent`s (e.g., wraps confluent producer).
2. Pass run metadata (IDs, pickup time, runner) and channel reminder settings to `schedule_for_run`.
3. Deploy `ReminderWorker` wired to the Slack DM sender and Kafka consumer. The worker reuses the same `ReminderPayload` schema defined in `coffeebuddy.infra.kafka.models`.

## Extensibility
- Additional reminder types can be added by extending `ReminderType` and mapping new behaviors in both scheduler and worker.
- Backoff/ retry logic remains centralized in the Kafka consumer; the worker re-raises errors for upstream retry policies.