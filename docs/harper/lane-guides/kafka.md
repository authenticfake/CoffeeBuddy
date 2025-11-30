## Lane Guide — kafka

### Tools
- tests: `pytest` with `pytest-kafka` or `confluent-kafka` mocks
- lint: `ruff` for producers/consumers code
- types: `mypy` focusing on DTOs under `app.shared.events`
- security: `kafkacat` ACL verification scripts
- build: container image via `docker build -f Dockerfile.kafka`

### CLI Examples
- Local: `docker compose up -d kafka zookeeper && pytest tests/kafka`
- Containerized: `docker compose run --rm kafka-tests pytest tests/kafka`

### Default Gate Policy
- min coverage: 80% for consumer/producer packages
- max criticals: 0 failing contract tests, 0 unauthenticated broker connections

### Enterprise Runner Notes
- SonarQube: enable custom quality profile for event DTOs
- Jenkins: pipeline stage spins up ephemeral Kafka via Kubernetes DinD, artifacts include schema registry compat report

### TECH_CONSTRAINTS integration
- air-gap: broker images pulled from `harbor.corp.local/confluentinc`
- registries: internal Schema Registry endpoints only; configure SASL/OAuth per OIDC policy