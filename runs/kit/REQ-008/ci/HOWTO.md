# HOWTO — REQ-008 Execution

## Prerequisites
- Python 3.12 with `pip`.
- Access to a Postgres instance reachable from your shell.
- `psql` CLI for running the upgrade/downgrade scripts.
- Environment variable `TEST_DATABASE_URL` (or `DATABASE_URL`) pointing to the Postgres database to use for migration tests.
- Optional: Docker Desktop if you plan to start a disposable Postgres container for local testing.

## Environment Setup
```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r runs/kit/REQ-008/requirements.txt
export TEST_DATABASE_URL="postgresql://user:pass@127.0.0.1:5432/coffeebuddy_test"
```

### Alternative: Editable install
If integrating into a mono-repo virtualenv, add the kit path to `PYTHONPATH`:
```bash
export PYTHONPATH="$(pwd)/runs/kit/REQ-008/src:${PYTHONPATH}"
```

## Running Migrations
```bash
export DATABASE_URL="$TEST_DATABASE_URL"
bash runs/kit/REQ-008/scripts/db_upgrade.sh
# To revert:
bash runs/kit/REQ-008/scripts/db_downgrade.sh
```

## Tests
```bash
pytest -q runs/kit/REQ-008/test
```
The migration tests will automatically skip if `TEST_DATABASE_URL`/`DATABASE_URL` is unset or Postgres is unreachable.

## CI / Enterprise Runner Notes
- Jenkins: configure a pipeline stage that installs `requirements.txt`, exports `TEST_DATABASE_URL`, then runs the LTC command (`pytest -q runs/kit/REQ-008/test`).
- Sonar/Mendix: not required for this REQ; mark as N/A.
- Reports: direct pytest to emit JUnit via `pytest --junitxml=runs/kit/REQ-008/reports/junit.xml runs/kit/REQ-008/test`.

## Troubleshooting
- **`psql: could not connect`**: verify network access and credentials in `DATABASE_URL`.
- **`uuid-ossp` missing**: ensure the Postgres instance allows `CREATE EXTENSION "uuid-ossp"`; contact DBAs if restricted.
- **Foreign key errors during tests**: drop/recreate the test database before re-running migrations to guarantee a clean slate.