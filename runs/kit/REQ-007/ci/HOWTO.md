# HOWTO — REQ-007 Kafka Infrastructure

## Prerequisites
- Python 3.12
- Access to the enterprise Kafka cluster or a local broker listening on `localhost:9092`.
- Ability to install the dependencies in `runs/kit/REQ-007/requirements.txt`.
- Optional: Prometheus endpoint to scrape metrics exported by the worker processes.

## Environment Setup
```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r runs/kit/REQ-007/requirements.txt
export KAFKA_BOOTSTRAP_SERVERS=localhost:9092
```

If SASL is required, also export `KAFKA_SECURITY_PROTOCOL`, `KAFKA_SASL_MECHANISM`, `KAFKA_SASL_USERNAME`, and `KAFKA_SASL_PASSWORD`.

## Running Tests
```bash
pytest -q runs/kit/REQ-007/test
```

This matches the `ci/LTC.json` contract.

## Using the Kafka Utilities

### Producers
```python
from coffeebuddy.infra.kafka import KafkaSettings, KafkaEventProducer, KafkaEvent, RUN_EVENTS_TOPIC

settings = KafkaSettings.from_env()
producer = KafkaEventProducer(settings)
await producer.start()
event = KafkaEvent(event_type="run_created", correlation_id="corr-id", payload={"run_id": "123"})
await producer.send(RUN_EVENTS_TOPIC, event, key="123")
await producer.stop()
```

### Consumers
```python
from coffeebuddy.infra.kafka import KafkaSettings, KafkaEventConsumer, REMINDER_EVENTS_TOPIC

async def handler(event):
    ...

settings = KafkaSettings.from_env()
consumer = KafkaEventConsumer(settings, REMINDER_EVENTS_TOPIC, group_id="worker", handler=handler)
await consumer.start()
...
await consumer.stop()
```

### Reminder Worker Harness
Integrate the reminder worker with the consumer by passing `worker.process_event` as the handler:

```python
from coffeebuddy.infra.kafka import ReminderWorker

worker = ReminderWorker(sender=my_sender)
consumer = KafkaEventConsumer(settings, REMINDER_EVENTS_TOPIC, "reminder-worker", worker.process_event)
```

Expose Prometheus metrics via your existing /metrics endpoint to capture counters defined in `coffeebuddy.infra.kafka.metrics`.

## Enterprise Runner Notes
- Jenkins: configure a pipeline step to install dependencies via the provided requirements file and execute the pytest command.
- Sonar/Mendix: not required for this slice; reuse global quality gates if desired.

## Troubleshooting
- **Module not found:** ensure `PYTHONPATH` includes `runs/kit/REQ-007/src` (e.g., `export PYTHONPATH=$PYTHONPATH:runs/kit/REQ-007/src`).
- **Kafka connection failures:** verify bootstrap servers and SASL credentials. Check firewall rules when running locally.
- **Prometheus metrics missing:** confirm the process registers counters before exposing `/metrics`; importing `coffeebuddy.infra.kafka.metrics` is sufficient.