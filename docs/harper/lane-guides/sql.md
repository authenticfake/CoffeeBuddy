## Lane Guide — sql

### Tools

- tests: pytest with fixtures spinning up Postgres containers, or platform provided test databases
- lint: sqlfluff or internal SQL linters following enterprise style guides
- types: schema validation via migration tool introspection, not traditional typing
- security: database permission reviews, scripts checked for use of least privilege roles
- build: migration tooling such as Alembic or Flyway, executed via CI jobs

### CLI Examples

- Local:
  - Start Postgres: `docker run --rm -e POSTGRES_PASSWORD=pass -p 5432:5432 postgres:16`
  - Run migrations: `alembic upgrade head`
  - Run DB tests: `pytest -m db`
- Containerized:
  - Use docker compose or platform templates to run app plus Postgres
  - Execute migrations in init container or CI migration job

### Default Gate Policy

- min coverage: tests must exercise all migrations up and down at least once in CI
- max criticals: zero critical SQL injection or privilege escalation issues from reviews
- integrity: all foreign keys not null constraints and enums validated via tests

### Enterprise Runner Notes

- SonarQube: limited direct SQL analysis, but include schema definitions as part of documentation
- Jenkins: dedicated DB migration stage, abort pipeline if migrations fail or checksum mismatches
- Artifacts: store migration scripts and generated schema diagrams in artifact repository

### TECH_CONSTRAINTS integration

- air-gap: base Postgres images mirrored internally, migration tools installed from internal package mirrors
- registries: database connection endpoints use internal hostnames and ports only
- tokens: DB credentials provisioned via Vault into CI and runtime, use short lived credentials when available