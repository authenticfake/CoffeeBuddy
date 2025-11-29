## Lane Guide — sql

### Tools
- tests: `pytest` with `pg_tmp` or `testcontainers` (internal registry image).
- lint: `sqlfluff` with Postgres dialect.
- types: not applicable; enforce via migrations validation.
- security: `psql --set ON_ERROR_STOP=on` with access control checks.
- build: `alembic upgrade head` packaged into Kubernetes job manifest.

### CLI Examples
- Local: `poetry run alembic upgrade head`.
- Containerized: `docker run --rm -v $PWD:/db registry.corp.local/dbtools:latest alembic upgrade head`.

### Default Gate Policy
- min coverage: migration smoke suite must pass; schema diff clean.
- max criticals: 0 failed migrations or lint errors.

### Enterprise Runner Notes
- SonarQube: SQL lint results uploaded as external issues.
- Jenkins: DB lane runs inside restricted network with Vault-injected creds; artifacts are migration logs.

### TECH_CONSTRAINTS integration
- air-gap: connect to staging Postgres via bastion proxy only.
- registries: DB tool images pulled from `registry.corp.local/dbtools`.