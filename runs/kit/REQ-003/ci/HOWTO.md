# HOWTO — REQ-003 Run Close Workflow

## Prerequisites
- Python 3.12
- Poetry or pip
- Access to required private package index (if any) configured via pip config
- Local Postgres/Kafka are not required for unit tests (SQLite is used)

## Setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r runs/kit/REQ-003/requirements.txt
```

## Running Tests
```bash
pytest -q runs/kit/REQ-003/test
```

## Enterprise Runner Notes
- Jenkins: add a pipeline stage executing the same pytest command.
- Sonar/Mend: hook into upstream CI; this KIT does not include specific scanners.

## Environment Configuration
- `PYTHONPATH` automatically resolved by pytest; set `export PYTHONPATH=$PWD` if running tools directly.
- No secrets required for unit tests; production wiring must inject DB/Kafka creds via Vault.

## Artifacts
- Tests: `runs/kit/REQ-003/test`
- Source: `runs/kit/REQ-003/src/coffeebuddy/core/runs`, `.../services/fairness`
- Docs: `runs/kit/REQ-003/docs`

## Troubleshooting
- **ImportError**: ensure `PYTHONPATH` includes repo root.
- **Missing deps**: confirm `requirements.txt` installed.
- **SQLite issues**: delete local `__pycache__` and rerun; schema is recreated each test.
```

KIT Iteration Log
- Targeted REQ-003 to deliver run-close fairness & summary functionality per PLAN and SPEC.
- In scope: fairness selector, close service, summaries, Kafka event publication, unit tests, docs, CI artifacts. Out of scope: Slack transport, reminder scheduling, admin flows.
- Tests: `pytest -q runs/kit/REQ-003/test`
- Prereqs: Python 3.12, pytest, SQLAlchemy per requirements. No external services.
- Dependencies & mocks: SQLite in-memory DB stands in for Postgres (permitted for tests). Kafka publisher/authorizer mocked for determinism.
- Product Owner Notes: Fairness explanation surfaces in summary for transparency; consecutive runner only when sole eligible participant or explicitly allowed.
- RAG citations: Leveraged PLAN.md (module namespaces), SPEC.md (acceptance criteria), plan.json (lane), TECH_CONSTRAINTS.yaml (runtime constraints), REQ-006 schema context for ORM models, REQ-007 Kafka topic definitions for run events.

```json
{
  "index": [
    {
      "req": "REQ-003",
      "src": [
        "runs/kit/REQ-003/src/coffeebuddy/core/runs",
        "runs/kit/REQ-003/src/coffeebuddy/services/fairness"
      ],
      "tests": [
        "runs/kit/REQ-003/test/test_close_run_service.py",
        "runs/kit/REQ-003/test/test_fairness_selector.py"
      ]
    }
  ]
}