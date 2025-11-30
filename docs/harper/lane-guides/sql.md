## Lane Guide — sql

### Tools
- tests: `pytest` + `pytest-postgresql` fixtures or `pg_prove`
- lint: `sqlfluff lint --dialect postgres`
- types: schema validation via `schemainspect`
- security: `psql -c "\dr"` review for least-privilege roles
- build: `alembic upgrade head` (migrations packaged)

### CLI Examples
- Local: `docker compose up -d postgres && alembic upgrade head && pytest tests/data`
- Containerized: `docker compose run --rm db-migrations alembic upgrade head`

### Default Gate Policy
- min coverage: 80% on repository layer
- max criticals: 0 failed migrations, 0 SQLFluff violations

### Enterprise Runner Notes
- SonarQube: enable SQL analyzer ruleset, upload via Jenkins post-step
- Jenkins: stage `db-migrate` executes migrations against ephemeral DB, artifacts stored as migration bundles

### TECH_CONSTRAINTS integration
- air-gap: base Postgres image from internal registry `harbor.corp.local/postgres`
- registries: alembic container image pinned and mirrored internally; no internet access during CI