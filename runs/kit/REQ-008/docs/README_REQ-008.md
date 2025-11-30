# REQ-008 — Database Schema & Persistence Layer

This KIT introduces CoffeeBuddy's foundational persistence layer.

## Contents
- `src/storage/schema.yaml`: engine-neutral schema specification.
- `src/storage/sql/`: versioned migrations (V0001 up/down).
- `src/storage/seed/seed.sql`: idempotent pilot channel seed data (10 rows).
- `scripts/db_upgrade.sh` / `db_downgrade.sh`: helper wrappers around `psql`.
- `src/coffeebuddy/infrastructure/db/`: SQLAlchemy models, session wiring, repositories.
- Tests under `test/`: Postgres migration smoke + repository unit tests.

## Usage Overview
1. Install dependencies from `requirements.txt`.
2. Export `DATABASE_URL` or `TEST_DATABASE_URL`.
3. Run `scripts/db_upgrade.sh` to apply the schema.
4. Execute `pytest -q runs/kit/REQ-008/test` to validate migrations and repositories.

Repositories expose high-level methods (`ensure_user`, `create_run`, `upsert_order`, etc.) ready to be injected into domain services implemented in subsequent REQs.