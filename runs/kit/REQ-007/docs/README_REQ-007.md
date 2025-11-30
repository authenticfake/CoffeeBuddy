# CoffeeBuddy — REQ-007

This REQ delivers the observability foundation:

- `coffeebuddy.observability.correlation`: correlation ID helpers.
- `coffeebuddy.observability.logging`: JSON logging configuration.
- `coffeebuddy.observability.metrics`: Prometheus counters/histograms.
- `coffeebuddy.observability.middleware`: FastAPI/Starlette middleware for correlation IDs and error handling.
- `coffeebuddy.observability.errors`: domain-safe exception types.

Use `build_metrics_suite()` when composing the ASGI app so all counters share a single registry. Wrap Slack/Kong ingress routes with both `CorrelationIdMiddleware` and `ErrorHandlingMiddleware` to guarantee tracing and user-safe responses.

Tests live under `test/observability`.