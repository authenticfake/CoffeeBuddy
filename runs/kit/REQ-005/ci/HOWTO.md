# HOWTO — Execute REQ-005 Validations

## Prerequisites
- Python 3.12 available on the runner.
- Network access to install PyPI dependencies (`sqlalchemy`, `pytest`).
- No database or Slack connectivity is required; tests run against SQLite in-memory DBs.
- Ensure `PYTHONPATH` includes `runs/kit/REQ-005/src` so CoffeeBuddy modules resolve.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r runs/kit/REQ-005/requirements.txt
export PYTHONPATH="runs/kit/REQ-005/src"
```

## Local / Container Execution
```bash
PYTHONPATH=runs/kit/REQ-005/src pytest -q runs/kit/REQ-005/test
```

## Enterprise Runners
- **Jenkins:** add a pipeline step `sh 'PYTHONPATH=runs/kit/REQ-005/src pytest -q runs/kit/REQ-005/test'` after installing requirements.
- **Sonar/Mend:** not required for this slice; no code scanning hooks introduced.
- **Artifacts:** pytest output is emitted to stdout; add `--junitxml=reports/junit.xml` if CI artifacts are needed.

## Environment Setup Tips
- Prefer `PYTHONPATH` overrides to avoid editing sys.path in production code.
- When running multiple KITs, activate the corresponding virtual environment per slice or install all requirements at repo root.

## Troubleshooting
- **Import errors:** confirm `PYTHONPATH` points to `runs/kit/REQ-005/src`.
- **Missing SQLite driver:** ensure Python was compiled with `pysqlite` (default on CPython builds); otherwise install `pysqlite3`.
- **Dependency conflicts:** recreate the virtual environment and reinstall `requirements.txt`.