from coffeebuddy.infra.kafka.topics import (
    ACL_REQUIREMENTS,
    REMINDER_EVENTS_TOPIC,
    RUN_EVENTS_TOPIC,
    TOPIC_REGISTRY,
)


def test_topic_registry_contains_expected_topics() -> None:
    topic_names = {topic.name for topic in TOPIC_REGISTRY}
    assert RUN_EVENTS_TOPIC.name in topic_names
    assert REMINDER_EVENTS_TOPIC.name in topic_names
    assert RUN_EVENTS_TOPIC.retention_ms == 7 * 24 * 60 * 60 * 1000
    assert REMINDER_EVENTS_TOPIC.retention_ms == 24 * 60 * 60 * 1000


def test_acl_requirements_cover_topics() -> None:
    resources = {acl.resource for acl in ACL_REQUIREMENTS}
    assert f"Topic:{RUN_EVENTS_TOPIC.name}" in resources
    assert f"Topic:{REMINDER_EVENTS_TOPIC.name}" in resources