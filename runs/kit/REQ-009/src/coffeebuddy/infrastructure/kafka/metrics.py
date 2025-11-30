from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from prometheus_client import CollectorRegistry, Counter, Histogram, REGISTRY


@dataclass(frozen=True)
class KafkaMetrics:
    publish_total: Counter
    publish_latency_seconds: Histogram
    consume_total: Counter
    consume_latency_seconds: Histogram
    consume_lag_seconds: Histogram

    @classmethod
    def create(cls, registry: Optional[CollectorRegistry] = None) -> "KafkaMetrics":
        reg = registry or REGISTRY
        return cls(
            publish_total=Counter(
                "coffeebuddy_kafka_publish_total",
                "Total Kafka publish attempts by topic/outcome.",
                labelnames=("topic", "outcome"),
                registry=reg,
            ),
            publish_latency_seconds=Histogram(
                "coffeebuddy_kafka_publish_latency_seconds",
                "Kafka publish latency.",
                labelnames=("topic",),
                buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5),
                registry=reg,
            ),
            consume_total=Counter(
                "coffeebuddy_kafka_consume_total",
                "Total Kafka messages consumed by topic/outcome.",
                labelnames=("topic", "outcome"),
                registry=reg,
            ),
            consume_latency_seconds=Histogram(
                "coffeebuddy_kafka_consume_latency_seconds",
                "Handler processing time per Kafka message.",
                labelnames=("topic",),
                buckets=(0.005, 0.01, 0.05, 0.1, 0.25, 0.5, 1.0),
                registry=reg,
            ),
            consume_lag_seconds=Histogram(
                "coffeebuddy_kafka_consume_lag_seconds",
                "Observed lag between message timestamp and handling.",
                labelnames=("topic",),
                buckets=(0.1, 0.5, 1, 2, 5, 10, 30, 60),
                registry=reg,
            ),
        )


DEFAULT_METRICS = KafkaMetrics.create()