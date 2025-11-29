# REQ-007 — Kafka Topics & Reminder Harness

## Scope
Implements the shared Kafka infrastructure required by CoffeeBuddy:
- Topic definitions with ACL notes.
- Structured event models.
- Async producer/consumer utilities for consistent observability.
- Reminder worker harness handling runner and last-call reminders.

## Components
| Module | Description |
| --- | --- |
| `coffeebuddy.infra.kafka.topics` | Declarative topic & ACL catalog for provisioning. |
| `coffeebuddy.infra.kafka.config` | Settings loader bound to environment variables. |
| `coffeebuddy.infra.kafka.models` | Typed Kafka event schemas, including reminder payloads. |
| `coffeebuddy.infra.kafka.producer` | Metrics-aware producer wrapper. |
| `coffeebuddy.infra.kafka.consumer` | Graceful consumer harness for services/workers. |
| `coffeebuddy.infra.kafka.reminder_worker` | Reminder processing logic with sender abstraction. |
| `coffeebuddy.infra.kafka.metrics` | Prometheus counters/histograms referenced by other slices. |

## Usage Notes
1. Always bootstrap producers/consumers with `KafkaSettings.from_env()` to respect platform configuration.
2. Topics must be referenced via `RUN_EVENTS_TOPIC` / `REMINDER_EVENTS_TOPIC`. No ad-hoc names.
3. Reminder worker should be composed with the consumer by passing `ReminderWorker.process_event` as the handler, and injecting a sender that interfaces with Slack DM helpers from REQ-001.

## Next Steps
- REQ-004 will consume `ReminderWorker` and `REMINDER_EVENTS_TOPIC`.
- Future slices may extend `TopicConfig` registry but must keep backward-compatible names.

## Tests
Run `pytest -q runs/kit/REQ-007/test` after installing requirements listed in `runs/kit/REQ-007/requirements.txt`.

KIT Iteration Log
-----------------
- **Targeted REQ-ID(s)**: REQ-007 (per plan dependency order; Kafka plumbing required before reminder app logic).
- **In/Out of scope**: Implemented topics, producer/consumer utilities, reminder worker harness, metrics, docs, LTC/HOWTO; out of scope—higher-level reminder workflows (REQ-004) and Slack integrations.
- **How to run tests**: `pytest -q runs/kit/REQ-007/test`
- **Prerequisites**: Python 3.12, ability to install dependencies from `runs/kit/REQ-007/requirements.txt`, Kafka bootstrap settings via env.
- **Dependencies and mocks**: Real aiokafka remains the production path; tests inject stub factories to avoid broker dependency, satisfying determinism.
- **Product Owner Notes**: Reminder worker currently focuses on per-event dispatch; extend sender implementation in REQ-004 to integrate Slack DM + metrics wiring.
- **RAG citations**: No prior KIT implementation context available in prompt; design derived directly from SPEC/PLAN.