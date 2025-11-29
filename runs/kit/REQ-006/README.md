# REQ-006 — Postgres Schema and DB Infrastructure

This kit defines the canonical CoffeeBuddy persistence model, migrations, seeds, and Python access helpers.

## Layout

```
runs/kit/REQ-006/
├── src
│   ├── coffeebuddy/infra/db          # SQLAlchemy models + session factory
│   └── storage
│       ├── spec/schema.yaml          # engine-neutral canonical schema
│       ├── sql/V0001.up.sql          # generated DDL
│       └── sql/V0001.down.sql
│       └── seed/seed.sql             # idempotent pilot seed data
├── scripts
│   ├── db_upgrade.sh
│   └── db_downgrade.sh
├── test/test_migration_sql.py        # migration + seed verification
├── requirements.txt
└── config/database.env.example
```

## Usage

1. **Install dependencies**

   ```bash
   pip install -r runs/kit/REQ-006/requirements.txt
   ```

2. **Apply migrations**

   ```bash
   export DATABASE_URL="postgresql://user:pass@host:5432/db"
   bash runs/kit/REQ-006/scripts/db_upgrade.sh
   ```

3. **Run seeds**

   ```bash
   psql "$DATABASE_URL" -f runs/kit/REQ-006/src/storage/seed/seed.sql
   ```

4. **Create SQLAlchemy sessions**

   ```python
   from coffeebuddy.infra.db import create_session_factory
   SessionFactory = create_session_factory()
   session = SessionFactory()
   ```

   If Vault credentials are required, set `VAULT_ADDR`, `VAULT_TOKEN`, and `VAULT_DB_SECRET_PATH`.

5. **Tests**

   ```bash
   pytest -q runs/kit/REQ-006/test
   ```

## Notes

- The schema is driven from `schema.yaml` and rendered to SQL; do not hand-edit SQL without updating the spec.
- Seeds insert 10 pilot-ready channels and can be re-run safely.
- Session factory automatically retries Vault fetches and uses the psycopg driver with pool pre-ping enabled.