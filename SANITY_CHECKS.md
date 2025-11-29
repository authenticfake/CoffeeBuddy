## SANITY_CHECKS

### Checklist
- [ ] `poetry install`
- [ ] `poetry run alembic upgrade head`
- [ ] `poetry run pytest -q`
- [ ] `poetry run ruff check src`
- [ ] `poetry run mypy src`
- [ ] `docker compose config`
- [ ] `poetry run uvicorn coffeebuddy.api.main:app --help`
- [ ] `curl -f http://localhost:${SERVICE_PORT}/health/ready`
- [ ] `curl -f http://localhost:${SERVICE_PORT}/metrics`
- [ ] Kafka smoke: `kafkacat -b ${KAFKA_BOOTSTRAP_SERVERS} -t coffeebuddy.run.events -C -o -1 -e`

### Expected Outputs & Fixes
- **Pytest** returns exit code 0; failures typically stem from missing env vars—load `.env.test` or export stubs.
- **Ruff/mypy** should show “no issues found”; if not configured, ensure `pyproject.toml` includes tool settings before running CI.
- **Uvicorn help** confirms entrypoint importable; ModuleNotFound errors indicate missing `src` on `PYTHONPATH`.
- **Health endpoints** return JSON `{"status": "ok"}`; DB/Vault issues surface as readiness failures—validate secrets and connectivity.
- **Metrics endpoint** must include `coffeebuddy_runs_total`, `coffeebuddy_run_duration_seconds_bucket`, `coffeebuddy_errors_total`; missing metrics mean instrumentation not initialized.
- **Kafka tail** should reveal JSON events with `correlation_id`; schema mismatch errors require updating producer payloads to match `coffeebuddy.infra.kafka.schemas`.

### Postman / API Validation
- Import generated collection (`docs/postman/CoffeeBuddy.postman_collection.json`).
- Set environment variables: `base_url`, `slack_signature`, `slack_timestamp`.
- Run “Slash Command Ack” request and verify 200 with ephemeral Slack payload stub.
- Run “Interaction Callback” request using stored `trigger_id`; expect 200 with block update.
- For failures with `invalid_signature`, ensure secrets align with Slack app config.