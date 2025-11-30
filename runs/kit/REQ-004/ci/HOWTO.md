# HOWTO — REQ-004

## Prerequisites
- Python 3.12 with `pip`.
- Access to the CoffeeBuddy repository checkout (this kit expects project root as working directory).
- Optional: virtualenv for isolation (`python -m venv .venv && source .venv/bin/activate`).

Install dependencies:
```bash
pip install -r runs/kit/REQ-004/requirements.txt
```
(Currently empty; reuse project-wide requirements if already installed.)

## Running Tests
All reminder slice tests:
```bash
pytest -q runs/kit/REQ-004/test
```

For richer output or coverage (optional):
```bash
pytest --maxfail=1 --disable-warnings -q runs/kit/REQ-004/test
```

## Local Usage
1. Ensure Kafka infra utilities from REQ-007 are available in `PYTHONPATH` (project root export already covers it).
2. Instantiate `ReminderScheduler` with the Kafka publisher from `coffeebuddy.infra.kafka`.
3. Wire `ReminderWorker` with the reminder Kafka consumer and inject `SlackReminderSender` using the Slack message dispatcher from `coffeebuddy.api.slack_runs`.

## Enterprise Runner (Jenkins/Sonar/etc.)
- Configure stage to run `pytest -q runs/kit/REQ-004/test` from repo root.
- Publish artifacts (if desired) by archiving `.pytest_cache` or junit reports generated via `pytest --junitxml=reports/junit.xml`.

## Environment Setup Tips
- Set `PYTHONPATH=.` to prefer in-repo modules.
- When running inside containers, mount repo at `/workspace` and execute commands from there.

## Troubleshooting
- **ImportError for `coffeebuddy.*`:** ensure you are running from repo root or `PYTHONPATH` includes it.
- **Kafka metrics modules missing:** verify REQ-007 artifacts are present; re-run `pip install -e .` if using editable setup.
- **Time-sensitive tests flake:** the worker tests rely on deterministic clocks; do not modify them to use real `asyncio.sleep`.