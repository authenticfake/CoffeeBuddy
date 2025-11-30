## SANITY_CHECKS

### Checklist
- [ ] `docker compose config`
- [ ] `uvicorn coffeebuddy.app:app --help`
- [ ] `curl -f http://localhost:8000/health/ready`
- [ ] `pytest -q`
- [ ] `ruff check`
- [ ] `mypy src`
- [ ] Kafka topics exist: `kafka-topics --bootstrap-server $KAFKA_BROKERS --list | grep coffeebuddy`
- [ ] Postman smoke: `/slack/command`, `/slack/interaction`
- [ ] Reminder worker log contains `reminder_sent` after scheduling test run

### Commands & Expected Output
- `docker compose config` → exits 0; prints merged config without warnings.
- `uvicorn coffeebuddy.app:app --help` → shows CLI usage; confirms FastAPI entrypoint available.
- `pytest -q` → `N passed` (ensure ≥80% coverage via CI).
- `ruff check` → no lint errors; fix via `ruff --fix`.
- `mypy src` → `Success: no issues found`; configure `mypy.ini` if needed.
- `kafka-consumer-groups --describe --group coffeebuddy-reminders` → verify lag ≈ 0.
- Postman run: Slack command returns `200` with `text="Coffee run started"`.
- Reminder smoke: create run with pickup+offset; `reminder-worker` logs `DM sent`.

### Common Fixes
- Missing Slack signature env: ensure `SLACK_SIGNING_SECRET` exported; otherwise API returns 401.
- DB migrations pending: run `alembic upgrade head`.
- Kafka ACL failures: confirm service principal matches `TopicACLRequirement` docs.
- Prometheus scrape errors: ensure `/metrics` reachable and `PROMETHEUS_MULTIPROC_DIR` set when using gunicorn.