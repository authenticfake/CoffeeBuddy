# KIT — REQ-006

## Scope
Implements the Postgres schema, migrations, seeds, SQLAlchemy models, and DB session factory required by Plan REQ-006.

## Decisions
- **Single source of truth**: `src/storage/spec/schema.yaml` documents entities; SQL scripts were rendered from it for traceability.
- **Idempotent migrations**: All DDL uses `IF NOT EXISTS`; scripts wrap in `BEGIN/COMMIT` and indexes use stable names for re-runs.
- **Seeds**: Ten pilot channels inserted via `ON CONFLICT DO UPDATE`, satisfying the seed cardinality guidance.
- **Session factory**: Real hvac-based Vault provider with linear backoff plus env fallbacks; creates psycopg-engineered SQLAlchemy sessions.
- **Models**: SQLAlchemy declarative models mirror the schema and expose deterministic `to_dict` serialization.

## Testing
`pytest -q runs/kit/REQ-006/test` uses `testcontainers` Postgres 16 to validate:
- Successful migration apply & schema shape.
- Seed idempotency (10 channels).
- Downgrade/upgrade roundtrip.

## Follow-ups
- Future REQs can extend `schema.yaml` and re-render SQL.
- Add Alembic integration if multi-version workflows grow.