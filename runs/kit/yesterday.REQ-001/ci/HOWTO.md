# HOWTO — Execute CI for REQ-001

## Prerequisites
- Python 3.12 available on PATH.
- Access to private package index if corporate policy requires.
- Network access to Kafka/Postgres hosts when running end-to-end (tests mock Kafka).
- Optional: virtual environment manager (`python -m venv .venv`).

## Setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r runs/kit/REQ-001/requirements.txt
```

## Running Tests
```bash
pytest -q runs/kit/REQ-001/test
```

## Runtime Execution
```bash
uvicorn coffeebuddy.app:app --host 0.0.0.0 --port 8000
```

Configure environment:
```bash
export COFFEEBUDDY_SLACK_SIGNING_SECRET=...
export COFFEEBUDDY_DATABASE_URL=postgresql+psycopg://user:pass@db:5432/coffeebuddy
export COFFEEBUDDY_KAFKA_BOOTSTRAP_SERVERS=broker1:9092,broker2:9092
```

## Enterprise Runner (Jenkins/Sonar)
- Jenkins: add steps `pip install -r runs/kit/REQ-001/requirements.txt` then `pytest -q runs/kit/REQ-001/test`.
- Sonar: run after tests and point to coverage if collected (not included here).

## Troubleshooting
- Signature errors: confirm system clock skew <5 minutes.
- DB connectivity: ensure `DATABASE_URL` reachable; enable `POOL_PRE_PING` already configured.
- Import issues: verify `PYTHONPATH` includes project root (`export PYTHONPATH=$PWD`).