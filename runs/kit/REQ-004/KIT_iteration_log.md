KIT Iteration Log
Targeted REQ‑ID(s) and rationale
- REQ-004: earliest open dependency; required for reminder scheduling/delivery slice.

In/Out of scope
- In scope: Kafka reminder payload scheduling, worker dispatch logic, unit tests, docs, LTC/HOWTO.
- Out of scope: Real Kafka producers, Slack DM implementation, scheduler invocation wiring from run lifecycle.

How to run tests
- `pytest -q runs/kit/REQ-004/test`

Prerequisites
- Python 3.12, pip, ability to set `PYTHONPATH=.` and install packages from `runs/kit/REQ-004/requirements.txt`.

Dependencies and mocks
- Kafka publishing mocked via `FakeProducer`.
- Slack reminder sending mocked via `StubSender`.
- No external services contacted; clock/sleep abstractions simulate timing.

Product Owner Notes
- Assumed reminders are scheduled once runner assignment is known; upstream flow should call scheduler post-assignment if earlier scheduling is required.

RAG citations
- Schema/entities alignment from `runs/kit/REQ-006/src/storage/spec/schema.yaml`.
- Channel/admin config behavior references `runs/kit/REQ-005/src/coffeebuddy/api/admin/service.py`.
- Kafka models/topics/worker baseline from `runs/kit/REQ-007/src/coffeebuddy/infra/kafka/models.py`, `topics.py`, and `reminder_worker.py`.

{
  "index": [
    {
      "req": "REQ-004",
      "src": [
        "runs/kit/REQ-004/src/coffeebuddy/jobs/reminders/__init__.py",
        "runs/kit/REQ-004/src/coffeebuddy/jobs/reminders/scheduler.py",
        "runs/kit/REQ-004/src/coffeebuddy/infra/kafka/reminder_worker.py"
      ],
      "tests": [
        "runs/kit/REQ-004/test/test_reminders.py"
      ]
    }
  ]
}