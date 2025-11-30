# KIT — REQ-008 (Postgres schema & repositories)

## Deliverables
- Canonical schema spec (`src/storage/schema.yaml`) plus V0001 migration pair, seeds, and upgrade/downgrade scripts.
- SQLAlchemy metadata, connection config, and repository facades in `coffeebuddy.infrastructure.db`.
- Unit tests for repository semantics (SQLite harness) and Postgres shape/seed verification requiring `TEST_DATABASE_URL`.

## Decisions & Notes
- JSON/YAML schema is treated as the source of truth; SQL and ORM models match its fields and constraints.
- Strict enum enforcement for run/admin types is implemented via `CHECK` constraints to remain engine-agnostic.
- Repository layer favours explicit transition validation and timestamp control for deterministic history.
- Tests skip gracefully when Postgres connectivity is unavailable, satisfying on-prem CI variability.

## Next Steps
- REQ-002 will build on these repositories to compose run lifecycle services.
- When Kafka integration (REQ-009) lands, repository transactions should be wrapped with event outbox logic.