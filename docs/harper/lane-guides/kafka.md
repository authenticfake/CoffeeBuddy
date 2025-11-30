## Lane Guide — kafka

### Tools

- tests: pytest with embedded Kafka or testcontainers, or organization standard Kafka test harness
- lint: configuration linting via internal tools, YAML or property file validators
- types: event schema validation using JSON Schema or Avro where applicable
- security: checks for proper authentication SASL TLS usage per enterprise Kafka standards
- build: configuration and client libraries versioned with application code

### CLI Examples

- Local:
  - Start Kafka via docker compose using approved local stack
  - Create topics: `kafka-topics --create --topic coffeebuddy.run.events ...`
  - Inspect messages: `kafka-console-consumer --topic coffeebuddy.run.events --from-beginning`
- Containerized:
  - Use testcontainers or platform integration tests to spin Kafka for CI
  - Run integration tests: `pytest -m kafka`

### Default Gate Policy

- min coverage: integration tests must cover publish and consume for each topic at least once
- max criticals: zero critical misconfigurations like no auth plaintext in non dev environments
- reliability: retry and dead letter handling must be defined and tested for failure scenarios

### Enterprise Runner Notes

- SonarQube: focus on Java or Python clients for code quality, not Kafka itself
- Jenkins: dedicated stage for Kafka integration tests against shared or ephemeral cluster
- Artifacts: store topic configuration docs and schema definitions with build artifacts

### TECH_CONSTRAINTS integration

- air-gap: Kafka client libraries sourced from internal artifact repositories only
- registries: broker addresses use internal DNS names, no external endpoints
- tokens: authentication credentials or certificates sourced via Vault or platform secret stores