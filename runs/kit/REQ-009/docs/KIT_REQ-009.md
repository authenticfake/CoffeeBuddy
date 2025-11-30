# KIT — REQ-009 (Kafka topics & client wrappers)

## Scope
- Define Kafka topic metadata and registry.
- Provide env-driven Kafka configuration (producers/consumers).
- Implement producer & consumer abstractions with metrics instrumentation.
- Supply unit tests and CI/HowTo assets.

## Design Overview
- `coffeebuddy.infrastructure.kafka.config`
  - `KafkaConfig` reads env vars, exposes helper methods for AIOKafka args and topic naming.
  - `ConsumerSettings` captures per-worker behavior.
- `topics`
  - Declarative `TopicDefinition` and registry for `run.events` and `reminder.events`.
- `events`
  - `KafkaRecord` envelope plus serializer/header helpers, guaranteeing deterministic JSON serialization.
- `metrics`
  - `KafkaMetrics` bundles Prometheus counters/histograms; `DEFAULT_METRICS` used by runtime components.
- `producer`
  - `KafkaProducerFactory` builds `AIOKafkaProducer`.
  - `KafkaEventPublisher` publishes `KafkaRecord` instances with structured logging, latency/failure metrics, and typed errors.
- `consumer`
  - `KafkaConsumerFactory` builds `AIOKafkaConsumer`.
  - `KafkaConsumerWorker` drives the consumer lifecycle, calls injected handlers, handles commits, and emits metrics + lag observations.

## Testing
- `test_topics.py`: prefix handling & metadata integrity.
- `test_producer.py`: success/error instrumentation on publishes.
- `test_consumer.py`: worker happy-path commits and error propagation with metrics.

Run tests via:
```bash
pip install -r runs/kit/REQ-009/requirements.txt
pytest -q runs/kit/REQ-009/test
```

## Extensibility
- Future REQs can add topic definitions and domain-specific handlers without altering existing wrappers.
- Metrics registry can be swapped per-app by injecting `KafkaMetrics.create(registry)` into publishers/consumers.
- Consumer worker is handler-agnostic, enabling reuse for reminder workers, analytics sinks, etc.