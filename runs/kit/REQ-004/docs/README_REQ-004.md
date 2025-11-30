# REQ-004 — Reminder Scheduling & Delivery

| Item | Detail |
| --- | --- |
| Lane | App / reminders |
| Entry Point | `coffeebuddy.jobs.reminders` |

## Components
- `ReminderScheduler`: emits `KafkaEvent`s to `coffeebuddy.reminder.events` with consistent payloads.
- `ReminderWorker`: consumes reminder events, waits for the configured tolerance window, and invokes a `ReminderSender`.
- `SlackReminderSender`: bridges the worker with Slack DM helpers living under `coffeebuddy.api.slack_runs`.

## Usage
```python
scheduler = ReminderScheduler(kafka_publisher)
scheduler.schedule(
    context=RunReminderContext(
        run_id=run.id,
        channel_id=channel.id,
        runner_user_id=run.runner_user_id,
        correlation_id=run.correlation_id,
    ),
    config=ChannelReminderConfig(
        channel_id=channel.id,
        reminders_enabled=channel.reminders_enabled,
        reminder_offset_minutes=channel.reminder_offset_minutes,
        last_call_enabled=channel.last_call_enabled,
        last_call_lead_minutes=channel.last_call_lead_minutes,
    ),
    pickup_time=run.pickup_time,
)
```

Worker wiring:
```python
sender = SlackReminderSender(slack_messenger, reminder_context_resolver)
worker = ReminderWorker(sender)

async for event in kafka_consumer:
    await worker.process_event(event)
```

## Testing
```
pytest -q runs/kit/REQ-004/test
```

## Notes
- Scheduler enforces future timestamps and skips reminders if disabled.
- Worker exports Prometheus metrics defined in `coffeebuddy.infra.kafka.metrics`.
- Slack sender requires a resolver capable of translating CoffeeBuddy IDs into Slack IDs; integrate with existing repositories or caches.