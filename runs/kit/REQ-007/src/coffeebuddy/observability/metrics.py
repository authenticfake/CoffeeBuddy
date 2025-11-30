from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from prometheus_client import CollectorRegistry, Counter, Histogram, generate_latest
from prometheus_client.exposition import CONTENT_TYPE_LATEST

__all__ = [
    "REQUEST_LATENCY_BUCKETS",
    "RUN_DURATION_BUCKETS",
    "RequestMetricsRecorder",
    "RunMetricsRecorder",
    "MetricsSuite",
    "build_metrics_suite",
    "render_registry",
    "PROMETHEUS_CONTENT_TYPE",
]

REQUEST_LATENCY_BUCKETS = (
    0.05,
    0.1,
    0.25,
    0.5,
    1,
    2,
    3,
    5,
)

RUN_DURATION_BUCKETS = (
    30,
    60,
    90,
    120,
    180,
    240,
    300,
    600,
)

PROMETHEUS_CONTENT_TYPE = CONTENT_TYPE_LATEST


class RequestMetricsRecorder:
    """Records request counts and latency for Slack + HTTP traffic."""

    def __init__(self, registry: CollectorRegistry) -> None:
        self._requests_total = Counter(
            "coffeebuddy_requests_total",
            "Total CoffeeBuddy requests partitioned by type and result.",
            labelnames=("type", "result"),
            registry=registry,
        )
        self._latency = Histogram(
            "coffeebuddy_request_latency_seconds",
            "Latency histogram for CoffeeBuddy endpoints.",
            labelnames=("type",),
            registry=registry,
            buckets=REQUEST_LATENCY_BUCKETS,
        )

    def observe(self, request_type: str, status_code: int, duration_seconds: float) -> None:
        result = "ok"
        if 400 <= status_code < 500:
            result = "client_error"
        elif status_code >= 500:
            result = "error"
        self._requests_total.labels(type=request_type, result=result).inc()
        self._latency.labels(type=request_type).observe(max(duration_seconds, 0.0))


class RunMetricsRecorder:
    """Tracks lifecycle metrics for coffee runs."""

    def __init__(self, registry: CollectorRegistry) -> None:
        self._runs_total = Counter(
            "coffeebuddy_runs_total",
            "Coffee runs started/completed/failed partitioned by status.",
            labelnames=("status",),
            registry=registry,
        )
        self._duration = Histogram(
            "coffeebuddy_run_duration_seconds",
            "Histogram of run durations from start to close.",
            labelnames=("status",),
            registry=registry,
            buckets=RUN_DURATION_BUCKETS,
        )

    def record(self, status: str, duration_seconds: Optional[float] = None) -> None:
        self._runs_total.labels(status=status).inc()
        if duration_seconds is not None:
            self._duration.labels(status=status).observe(max(duration_seconds, 0.0))


@dataclass(frozen=True)
class MetricsSuite:
    """Convenience container bundling registry and domain-specific recorders."""

    registry: CollectorRegistry
    request: RequestMetricsRecorder
    runs: RunMetricsRecorder


def build_metrics_suite(registry: Optional[CollectorRegistry] = None) -> MetricsSuite:
    """
    Create a CollectorRegistry seeded with all required counters/histograms.
    """
    registry = registry or CollectorRegistry()
    request_recorder = RequestMetricsRecorder(registry)
    run_recorder = RunMetricsRecorder(registry)
    return MetricsSuite(registry=registry, request=request_recorder, runs=run_recorder)


def render_registry(registry: CollectorRegistry) -> bytes:
    """
    Serialize the registry into Prometheus exposition format payload.
    """
    return generate_latest(registry)