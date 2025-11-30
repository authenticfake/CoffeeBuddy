# coffeebuddy.core.runs

## Overview
Provides the domain services for closing CoffeeBuddy runs:

1. **Authorization** — via injected `RunCloseAuthorizer`.
2. **Fairness** — `FairnessSelector` evaluates recent `Run` history per channel.
3. **Persistence** — updates `Run`, `Order`, and `RunnerStat` rows transactionally.
4. **Events** — emits `run_closed` & `runner_assigned` Kafka events through injected publisher.
5. **Summaries** — `RunSummaryBuilder` returns deterministic payloads for Slack channel + DM messages.

## Extension Points
- **Authorizer**: plug channel-admin logic or Slack role enforcement.
- **Publisher**: adapt to existing Kafka producer infrastructure.
- **Clock**: inject deterministic clocks for testing or replay.
- **Summary**: wrap `RunSummary` for rendering Slack blocks.

## Usage
```python
service = CloseRunService(
    session=session,
    fairness_selector=FairnessSelector(session),
    summary_builder=RunSummaryBuilder(),
    authorizer=my_authorizer,
    publisher=my_publisher,
)

result = service.close_run(
    CloseRunRequest(
        run_id="run-id",
        actor_user_id="user-id",
        correlation_id="corr-id",
    )
)
```

Consume `result.summary` for Slack messaging and rely on emitted Kafka events for downstream analytics/reminders.