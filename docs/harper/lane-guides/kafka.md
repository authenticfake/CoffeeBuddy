## Lane Guide — kafka

### Tools
- tests: `pytest` with `aiokafka` mocks or `kafka-python`, embedded broker via `kraft` container.
- lint: `ruff` for harness scripts.
- types: `mypy` on producer/consumer utilities.
- security: `kafkacat` ACL validation scripts.
- build: Docker image `registry.corp.local/coffee/kafka-tools`.

### CLI Examples
- Local: `poetry run pytest tests/kafka`.
- Containerized: `docker run --network corp-kafka registry.corp.local/coffee/kafka-tools bash -c "pytest tests/kafka && kcat -b broker:9092 -L"`.

### Default Gate Policy
- min coverage: 80% on kafka module.
- max criticals: 0 open CVEs on kafka client libs; consumer lag alerts none.

### Enterprise Runner Notes
- SonarQube: treat kafka harness as Python project with messaging profile.
- Jenkins: dedicated Kafka stage spins ephemeral broker via Docker-in-Docker; logs archived for ACL review.

### TECH_CONSTRAINTS integration
- air-gap: brokers reachable only on corp network; no public bootstrap.
- registries: kafka tool images from `registry.corp.local/coffee/kafka`.