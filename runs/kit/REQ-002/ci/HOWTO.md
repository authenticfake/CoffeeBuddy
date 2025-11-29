# HOWTO — Execute REQ-002 Tests

## Prerequisites
- Python 3.12 (per TECH_CONSTRAINTS profile `app-core`).
- Access to the repository root with the `runs/kit/REQ-002` folder.
- Network egress to install PyPI packages if dependencies are missing.

## Environment Setup
```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r runs/kit/REQ-002/requirements.txt
export PYTHONPATH=.
```

The `PYTHONPATH` export ensures the `coffeebuddy` modules under `runs/kit/REQ-002/src` resolve without an editable install.

## Running Tests
Execute from the repository root:

```bash
pytest -q runs/kit/REQ-002/test
```

This command matches the LTC contract and exercises the order + preference workflows.

## Enterprise Runner Guidance
- **Jenkins**: Add a pipeline stage that runs `pip install -r runs/kit/REQ-002/requirements.txt` followed by the pytest command above.
- **Sonar/Mendix/PLC**: No direct integration required for this slice; ensure Python 3.12 agents honor the same virtual environment steps.
- **Artifacts**: Pytest output is displayed in the console; attach the log to the job for traceability if desired.

## Troubleshooting
- **Import errors**: Confirm `PYTHONPATH=.` (or add `runs/kit/REQ-002/src` to `PYTHONPATH`). In CI, set it via environment configuration.
- **Missing SQLite driver**: Python’s built-in `pysqlite` is sufficient; ensure the interpreter was built with SQLite support.
- **Dependency install failures**: Verify outbound proxy settings or pre-bake dependencies into the runner image.

## Notes
No external services (DB/Kafka) are required; tests rely on SQLite in-memory databases for determinism.
```

## KIT Iteration Log
- **Targeted REQ-ID(s)**: REQ-002 (order capture & preference reuse). Focused on backend services to satisfy acceptance for modal validation, participant counts, preference updates, and order reuse.
- **In/Out of scope**: In scope – domain services, repositories, preference management, and unit tests. Out of scope – Slack transport glue, Kafka emissions, UI block builders.
- **How to run tests**: `pytest -q runs/kit/REQ-002/test`
- **Prerequisites**: Python 3.12, ability to install dependencies from `runs/kit/REQ-002/requirements.txt`, environment variable `PYTHONPATH=.`.
- **Dependencies and mocks**: SQLite in-memory DB substitutes Postgres during tests for determinism; no external mocks required beyond ORM fixtures.
- **Product Owner Notes**: Validation max length set to 280 chars (tune later if UX requires). Preference reuse automatically refreshes `last_used_at`.
- **RAG Citations**: Schema & ORM alignment referenced from `runs/kit/REQ-006/src/storage/sql/V0001.up.sql` and `runs/kit/REQ-006/src/coffeebuddy/infra/db/models.py`; plan alignment from `PLAN.md`.

```json
{
  "index": [
    {
      "req": "REQ-002",
      "src": [
        "runs/kit/REQ-002/src/coffeebuddy/core/orders",
        "runs/kit/REQ-002/src/coffeebuddy/services/preferences"
      ],
      "tests": [
        "runs/kit/REQ-002/test/test_order_service.py"
      ]
    }
  ]
}