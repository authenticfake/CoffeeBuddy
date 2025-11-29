# FINALIZE

## Checklist
- `docker compose -f deploy/docker-compose.yml config` → exits 0 to confirm manifest validity.
- `uvicorn --help` → ensures CLI entrypoint available inside virtualenv.
- `curl -f http://localhost:8080/health/ready` → returns HTTP 200 once API is ready.
- `pytest -q` → all suites green with ≥80% coverage.
- `ruff check src` → no lint errors (if `ruff.toml` present).
- `mypy src` → optional but recommended; should succeed given typed services.
- Postman collection smoke:
  - Send `/coffee` slash command request (mock Slack payload) → HTTP 200 with acknowledgment.
  - Trigger reminder event via Kafka or CLI → observe DM payload logged and `reminder_sent` metric increment.

## Expected Outputs & Fixes
- If `curl .../health/ready` fails, verify Postgres/Kafka connectivity and Vault credentials.
- `pytest` failures in reminder tests often indicate Kafka broker unavailable; ensure `kafka:9092` reachable or set `KAFKA_BOOTSTRAP_SERVERS=localhost:9092`.
- Lint/type failures typically stem from newly added modules lacking annotations; run `ruff --fix` and add typing stubs.
- Postman failures with signature errors mean `SLACK_SIGNING_SECRET` mismatch; update environment variables to match payload secret.

## Assumptions
- Compose stack includes Postgres, Kafka, and the API container; adjust commands for Helm-based environments.