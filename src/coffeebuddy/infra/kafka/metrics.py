from __future__ import annotations

from prometheus_client import Counter, Histogram

KAFKA_PRODUCE_TOTAL = Counter(
    "coffeebuddy_kafka_produce_total",
    "Number of Kafka messages produced.",
    ("topic", "status"),
)

KAFKA_CONSUME_TOTAL = Counter(
    "coffeebuddy_kafka_consume_total",
    "Number of Kafka messages consumed.",
    ("topic", "status"),
)

REMINDER_SEND_TOTAL = Counter(
    "coffeebuddy_reminder_send_total",
    "Reminder delivery attempts segmented by outcome.",
    ("reminder_type", "status"),
)

REMINDER_DELAY_SECONDS = Histogram(
    "coffeebuddy_reminder_delay_seconds",
    "Observed delay between scheduled reminder time and processing time.",
    buckets=(0.0, 5.0, 15.0, 30.0, 60.0, 120.0, float("inf")),
)