# CI / Execution HOWTO — REQ-009

## Prerequisites
- Python 3.12
- Access to internal package index or PyPI mirror for `aiokafka`, `prometheus-client`, `pytest`, `pytest-asyncio`.
- Local or remote Kafka cluster only required for manual integration tests (unit tests mock Kafka).

## Environment Setup
```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r runs/kit/REQ-009/requirements.txt
export PYTHONPATH="runs/kit/REQ-009/src:${PYTHONPATH}"
```

## Running Tests
```bash
pytest -q runs/kit/REQ-009/test
```

## Manual Producer/Consumer Smoke Test
1. Export Kafka connection vars (mapped from Vault secrets):
   ```bash
   export KAFKA_BOOTSTRAP_SERVERS="broker1:9092,broker2:9092"
   export KAFKA_CLIENT_ID="coffeebuddy-dev"
   export KAFKA_TOPIC_PREFIX="coffeebuddy"
   ```
2. Launch an async shell or script:
   ```python
   import asyncio
   from coffeebuddy.infrastructure.kafka import (
       KafkaConfig, KafkaProducerFactory, KafkaEventPublisher,
       KafkaRecord, TopicRegistry, RUN_EVENTS_TOPIC
   )

   async def main():
       cfg = KafkaConfig.from_env()
       topic = TopicRegistry(cfg.topic_prefix).resolve(RUN_EVENTS_TOPIC.slug)
       producer = KafkaProducerFactory(cfg).build()
       await producer.start()
       publisher = KafkaEventPublisher(producer)
       await publisher.publish(KafkaRecord(topic=topic, key="demo", value={"type": "run_created"}))
       await producer.stop()

   asyncio.run(main())
   ```
3. For consumer smoke tests, reuse `KafkaConsumerFactory` + `KafkaConsumerWorker` with a handler that prints payloads.

## Enterprise Runner Notes
- Jenkins/Argo: add a pipeline step `pip install -r runs/kit/REQ-009/requirements.txt && pytest -q runs/kit/REQ-009/test`.
- Ensure `PYTHONPATH` includes `runs/kit/REQ-009/src` for any lint/type jobs.
- Sonar/Mendix scanning should target the same directory; no extra build steps are required.

## Troubleshooting
- **Import errors**: confirm `PYTHONPATH` or use `pip install -e runs/kit/REQ-009/src`.
- **Missing aiokafka**: verify requirements installation succeeded; corporate mirrors might need `PIP_INDEX_URL`.
- **Kafka auth failures (manual tests)**: ensure SASL env vars match cluster configuration.
- **Prometheus duplicate metrics**: instantiate `KafkaMetrics.create(registry=CollectorRegistry())` per test to avoid re-registering.

KIT Iteration Log
- **Targeted REQ-ID(s)**: REQ-009 (kafka) — built topic registry, config helpers, producer/consumer wrappers, tests, and docs per SPEC/PLAN.
- **In Scope**: Kafka env config, topic definitions, producer & consumer abstractions with metrics, unit tests, CI artifacts.
- **Out of Scope**: Domain event generation, reminder/run handlers, actual Kafka cluster provisioning.
- **How to Run Tests**: `pip install -r runs/kit/REQ-009/requirements.txt && pytest -q runs/kit/REQ-009/test`
- **Prerequisites**: Python 3.12, pip access to aiokafka/prometheus-client/pytest; Kafka cluster only for manual integration.
- **Dependencies & Mocks**: AIOKafka producers/consumers mocked in unit tests; no external Kafka required.
- **Product Owner Notes**: Topic registry centralizes names; consumer worker exposes `wait()` for orchestration; metrics ready for Prometheus scrape.
- **RAG Citations**: Referenced PLAN.md (module boundaries, lane), SPEC.md (Kafka requirements), TECH_CONSTRAINTS.yaml (runtime/observability), prior infra patterns from REQ-010/REQ-008 snippets for consistency.

```json
{
  "index": [
    {
      "req": "REQ-009",
      "src": [
        "runs/kit/REQ-009/src/coffeebuddy/infrastructure/kafka"
      ],
      "tests": [
        "runs/kit/REQ-009/test/infrastructure/kafka"
      ]
    }
  ]
}