# HOWTO — Execute REQ-006 Assets

## Prerequisites
- Python 3.12
- Docker engine (for Testcontainers-based tests)
- `psql` client for migration scripts
- Access to Vault if production credentials are sourced dynamically

Install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r runs/kit/REQ-006/requirements.txt
```

## Environment Setup
Create a `.env` from `config/database.env.example` and export:

```bash
source runs/kit/REQ-006/config/database.env.example
```

If using Vault:

```bash
export VAULT_ADDR="https://vault.internal"
export VAULT_TOKEN="***"
export VAULT_DB_SECRET_PATH="kv/coffeebuddy/postgres"
```

Ensure `DATABASE_URL` is unset so the Vault provider is used.

## Running Migrations
Upgrade:

```bash
DATABASE_URL="postgresql://user:pass@host:5432/db" \
bash runs/kit/REQ-006/scripts/db_upgrade.sh
```

Downgrade:

```bash
DATABASE_URL="postgresql://user:pass@host:5432/db" \
bash runs/kit/REQ-006/scripts/db_downgrade.sh
```

Seeds:

```bash
psql "$DATABASE_URL" -f runs/kit/REQ-006/src/storage/seed/seed.sql
```

## Tests
Execute shape tests (requires Docker):

```bash
pytest -q runs/kit/REQ-006/test --junitxml=runs/kit/REQ-006/reports/junit.xml
```

If Docker is unavailable, set `PYTEST_ADDOPTS="--maxfail=1"` and tests will skip via the Testcontainers guard.

## CI/CD (Jenkins/Sonar etc.)
- Configure Jenkins pipeline to `pip install -r runs/kit/REQ-006/requirements.txt`.
- Run the LTC command from repo root.
- Archive `runs/kit/REQ-006/reports/junit.xml` for test visibility.
- Provide Docker socket access for Testcontainers.

## Troubleshooting
- **`DATABASE_URL required`**: export it or configure Vault paths before running scripts.
- **`testcontainers` failures**: ensure Docker daemon is running and the user has permission (`docker info`).
- **Import errors**: confirm virtualenv is active or add repo root to `PYTHONPATH`.
- **Vault permission issues**: verify token policy grants `read` on the configured secret path.

Artifacts are under `runs/kit/REQ-006/src` for migrations/specs and `runs/kit/REQ-006/test` for validation. 

KIT Iteration Log
-----------------
- **Targeted REQ-ID(s)**: REQ-006 (first open Infra dependency to unblock higher-level App REQs per PLAN).
- **In Scope**: Postgres schema spec, migrations, seeds, SQLAlchemy models, Vault-aware session factory, migration scripts, containerized tests, CI artifacts (LTC/HOWTO), docs.
- **Out of Scope**: Application services (Slack handlers, Kafka topics), additional migration versions, data retention jobs.
- **How to Run Tests**: `pytest -q runs/kit/REQ-006/test --junitxml=runs/kit/REQ-006/reports/junit.xml`
- **Prerequisites**: Python 3.12, Docker for Testcontainers, `psql` client, optional Vault access for prod credentials.
- **Dependencies and Mocks**: Real Postgres via Testcontainers; Vault client only instantiated when env vars provided (no mocks in production path).
- **Product Owner Notes**: Schema adheres to SPEC entities and PLAN namespaces; seeds deliver 10 pilot channels as requested.
- **RAG Citations**: SPEC.md (data model, retention requirements); PLAN.md & plan.json (namespace, acceptance criteria); TECH_CONSTRAINTS.yaml (runtime, coverage expectations).
```json
{
  "index": [
    {
      "req": "REQ-006",
      "src": [
        "runs/kit/REQ-006/src/storage/spec/schema.yaml",
        "runs/kit/REQ-006/src/storage/sql/V0001.up.sql",
        "runs/kit/REQ-006/src/storage/sql/V0001.down.sql",
        "runs/kit/REQ-006/src/storage/seed/seed.sql",
        "runs/kit/REQ-006/src/coffeebuddy/infra/db"
      ],
      "tests": [
        "runs/kit/REQ-006/test/test_migration_sql.py"
      ]
    }
  ]
}