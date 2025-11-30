# KIT — REQ-007 Observability

## Scope
REQ-007 adds the shared observability layer for CoffeeBuddy:

- Correlation ID context utilities and HTTP middleware.
- Structured JSON logging with correlation/run/channel metadata.
- Prometheus metrics suite for request/latency and run lifecycle.
- Error handling middleware that maps domain errors to Slack-safe payloads and records metrics.

## Design Highlights
- **ContextVar-based tracing** keeps request metadata thread/task safe.
- **JsonLogFormatter** ensures logs are machine parsable and secrets-free.
- **MetricsSuite** bundles registry plus domain recorders, easing reuse by future REQs.
- **ErrorHandlingMiddleware** cleanly separates user-facing messages from log-level detail.

## Tests
`pytest --junitxml=reports/junit.xml -q test`

Covers correlation middleware behavior, logging output, metric counters/histograms, and error middleware responses/metrics.