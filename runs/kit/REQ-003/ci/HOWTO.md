# HOWTO — REQ-003 Execution

## Prerequisites
- Python 3.12 with `pip`.
- Access to the repository root (commands assume they are run there).
- Network access to install PyPI packages listed in `runs/kit/REQ-003/requirements.txt`.

Optional (but recommended):
- Virtual environment: `python3 -m venv .venv && source .venv/bin/activate`.

## Dependency Installation
```bash
pip install -r runs/kit/REQ-003/requirements.txt
```

## Environment Setup
- Ensure `PYTHONPATH=.` so tests import the project packages:
  ```bash
  export PYTHONPATH=.
  ```
- No secrets or external services are required; SQLite is used for tests.

## Running Tests
```bash
mkdir -p runs/kit/REQ-003/reports
PYTHONPATH=. pytest -q runs/kit/REQ-003/test \
  --junitxml runs/kit/REQ-003/reports/junit.xml \
  --cov=runs/kit/REQ-003/src \
  --cov-report xml:runs/kit/REQ-003/reports/coverage.xml
```

## CI / Enterprise Runner Notes
- Jenkins/GitLab: use a Python 3.12 agent, install deps via the requirements file, set `PYTHONPATH=.` in the job, then run the command above.
- Sonar/Mend: consume the generated coverage XML at `runs/kit/REQ-003/reports/coverage.xml`.
- Artifacts: junit + coverage reports land under `runs/kit/REQ-003/reports/`.

## Troubleshooting
- **Import errors**: confirm `PYTHONPATH` includes the repo root.
- **Missing packages**: rerun `pip install -r runs/kit/REQ-003/requirements.txt`.
- **SQLite FK issues**: ensure tests run fresh; they auto-create in-memory DBs per test module.
```

---

**KIT Iteration Log**

- **Targeted REQ-ID(s)**: REQ-003 (run lifecycle close/fairness). Dependencies from PLAN enforced via shared models from REQ-006 and order context from REQ-002.
- **In Scope**: Fairness service, run-close orchestration, DTOs, and tests/docs/CI wiring per Output Contract. **Out of Scope**: Slack transport itself, reminder jobs (REQ-004), admin/UIs.
- **How to Run Tests**: `pip install -r runs/kit/REQ-003/requirements.txt && PYTHONPATH=. pytest -q runs/kit/REQ-003/test --junitxml runs/kit/REQ-003/reports/junit.xml --cov=runs/kit/REQ-003/src --cov-report xml:runs/kit/REQ-003/reports/coverage.xml`
- **Prerequisites**: Python 3.12, pip, local network to fetch PyPI packages; no external services required (SQLite-backed tests).
- **Dependencies and Mocks**: SQLAlchemy ORM models from REQ-006 reused; tests rely on in-memory SQLite plus timestamp injection (clock lambdas). No external mocks beyond lightweight authorizer stub.
- **Product Owner Notes**: Fairness rationale text is human-readable for Slack summaries; CloseRunService remains transaction-agnostic for reuse in API handlers.
- **RAG Citations**: SPEC.md (FR3–FR5, fairness requirements), PLAN.md (module boundaries, dependencies), docs/harper/plan.json (lane + dependency chain), REQ-006 artifacts (schema/models for users, channels, runs, orders, runner_stats).

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
        "runs/kit/REQ-003/test/test_fairness_service.py"
      ]
    }
  ]
}