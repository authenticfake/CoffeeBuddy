# REQ-009 — Kafka Infrastructure

## What’s Included
- Topic registry for `run.events` and `reminder.events`.
- Env-driven Kafka config helpers.
- Producer factory & `KafkaEventPublisher` with Prometheus metrics.
- Consumer factory & worker with handler injection and lag tracking.
- Unit tests plus CI artifacts (LTC/HOWTO).

## Usage
```python
from coffeebuddy.infrastructure.kafka import (
    KafkaConfig, KafkaProducerFactory, KafkaEventPublisher,
    KafkaRecord, TopicRegistry, RUN_EVENTS_TOPIC
)

config = KafkaConfig.from_env()
producer = KafkaProducerFactory(config).build()
await producer.start()

publisher = KafkaEventPublisher(producer)
topic = TopicRegistry(config.topic_prefix).resolve(RUN_EVENTS_TOPIC.slug)
await publisher.publish(KafkaRecord(topic=topic, key="run-123", value={"type": "run_created"}))
```

Consumers:
```python
from coffeebuddy.infrastructure.kafka import (
    ConsumerSettings, KafkaConsumerFactory, KafkaConsumerWorker
)
settings = ConsumerSettings(group_id="reminder-workers", topics=(topic,))
consumer = KafkaConsumerFactory(config, settings).build()

async def handler(record):
    ...

worker = KafkaConsumerWorker(consumer, handler, commit_on_success=True)
await worker.start()
```

Run tests:
```bash
pip install -r runs/kit/REQ-009/requirements.txt
pytest -q runs/kit/REQ-009/test