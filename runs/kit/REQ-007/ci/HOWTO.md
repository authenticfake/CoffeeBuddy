# HOWTO — REQ-007 Observability

## Prerequisites
- Python 3.12
- `pip` capable of installing wheels.
- Network access to fetch PyPI packages (or pre-populated internal mirror).

## Environment Setup
```bash
cd runs/kit/REQ-007
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Running Tests
```bash
cd runs/kit/REQ-007
pytest --junitxml=reports/junit.xml -q test
```

The command creates `reports/junit.xml`, which CI uses for normalization.

## CI / Enterprise Runner Tips
- Configure Jenkins/GitLab steps to run from repository root with `cwd=runs/kit/REQ-007`.
- Install dependencies via the provided `requirements.txt` before executing pytest.
- Publish `reports/junit.xml` as a JUnit artifact for enterprise dashboards (e.g., SonarQube ingestion).

## Observability Wiring
- Import `build_metrics_suite()` inside the ASGI factory to obtain a shared `CollectorRegistry`.
- Apply `CorrelationIdMiddleware` before other middleware touching logs to guarantee context.
- Wrap the app with `ErrorHandlingMiddleware` supplying the request metrics recorder.

## Troubleshooting
- **Import errors**: ensure `runs/kit/REQ-007/src` is on `PYTHONPATH` (pytest does this automatically via `pythonpath` manipulation). If running manually, `export PYTHONPATH=$(pwd)/src`.
- **Missing FastAPI/httpx**: rerun `pip install -r requirements.txt`.
- **Permission errors writing reports**: verify `runs/kit/REQ-007/reports` is writable or adjust report path consistently in LTC and commands.
```

KIT Iteration Log
- Targeted REQ-IDs: REQ-007 (observability foundation as per PLAN track App; required before Slack endpoints in REQ-001).
- In Scope: correlation ID utilities, structured logging config, Prometheus metrics suite, domain error types, FastAPI middleware with tests/docs/CICD artifacts.
- Out of Scope: wiring into production runtime, Slack-specific handlers, Kafka/db instrumentation (future REQs).
- Tests: `cd runs/kit/REQ-007 && pytest --junitxml=reports/junit.xml -q test`
- Prerequisites: Python 3.12, pip, ability to install fastapi/httpx/prometheus-client/pytest; no external services required.
- Dependencies & Mocks: FastAPI app + httpx ASGITransport used for middleware tests; no external IO. Metrics validated via in-memory CollectorRegistry.
- Product Owner Notes: Observability components align with SPEC latency/metrics/logging requirements and remain composable for upcoming Slack/API REQs.
- RAG Citations: Referenced PLAN.md for module ownership/lane guidance and SPEC.md observability requirements; leveraged REQ-010 FastAPI runtime context (health endpoints & app factory) to ensure seam compatibility.

{
  "index": [
    {
      "req": "REQ-007",
      "src": [
        "runs/kit/REQ-007/src/coffeebuddy/observability/__init__.py",
        "runs/kit/REQ-007/src/coffeebuddy/observability/correlation.py",
        "runs/kit/REQ-007/src/coffeebuddy/observability/logging.py",
        "runs/kit/REQ-007/src/coffeebuddy/observability/metrics.py",
        "runs/kit/REQ-007/src/coffeebuddy/observability/errors.py",
        "runs/kit/REQ-007/src/coffeebuddy/observability/middleware.py"
      ],
      "tests": [
        "runs/kit/REQ-007/test/observability/test_correlation_middleware.py",
        "runs/kit/REQ-007/test/observability/test_logging.py",
        "runs/kit/REQ-007/test/observability/test_metrics.py",
        "runs/kit/REQ-007/test/observability/test_error_middleware.py"
      ]
    }
  ]
}