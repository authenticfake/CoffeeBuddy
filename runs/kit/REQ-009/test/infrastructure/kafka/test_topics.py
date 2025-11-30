from coffeebuddy.infrastructure.kafka.config import KafkaConfig
from coffeebuddy.infrastructure.kafka.topics import (
    RUN_EVENTS_TOPIC,
    REMINDER_EVENTS_TOPIC,
    TopicRegistry,
)


def test_topic_registry_applies_prefix():
    config = KafkaConfig(bootstrap_servers=("broker1:9092",), topic_prefix="pilot")
    registry = TopicRegistry(config.topic_prefix)

    assert registry.resolve(RUN_EVENTS_TOPIC.slug) == "pilot.run.events"
    assert registry.resolve(REMINDER_EVENTS_TOPIC.slug) == "pilot.reminder.events"

    run_name, run_def = next(iter(registry.list()))
    assert run_name.startswith("pilot.")
    assert run_def.partitions == RUN_EVENTS_TOPIC.partitions