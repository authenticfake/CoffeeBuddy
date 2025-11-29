# CoffeeBuddy — REQ-001 (Slack Run Bootstrap)

## Overview
This slice delivers the `/coffee` slash command surface:
- Verifies Slack signatures.
- Persists a new `Run` record with metadata and correlation ID.
- Returns Slack blocks with CTA buttons (order, reuse, close).
- Emits a `run_created` Kafka event for downstream workflows.

## Environment Variables
| Variable | Description |
| --- | --- |
| `COFFEEBUDDY_SLACK_SIGNING_SECRET` | Slack signing secret (required). |
| `COFFEEBUDDY_DATABASE_URL` | SQLAlchemy URL (e.g., `postgresql+psycopg://user:pass@host:5432/db`). |
| `COFFEEBUDDY_KAFKA_BOOTSTRAP_SERVERS` | Kafka brokers list. |
| `COFFEEBUDDY_RUN_EVENTS_TOPIC` | Kafka topic for run events (default `coffeebuddy.run.events`). |

## Running locally
```bash
pip install -r runs/kit/REQ-001/requirements.txt
uvicorn coffeebuddy.app:app --reload
```

Send a Slack-style request (sample via curl):
```bash
curl -X POST http://localhost:8000/slack/commands \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "X-Slack-Request-Timestamp: $(date +%s)" \
  -H "X-Slack-Signature: <computed>" \
  --data 'team_id=T1&channel_id=C1&user_id=U1&text=pickup=2030-01-01T09:00:00+00:00 note=Lobby'
```

## Testing
```bash
pip install -r runs/kit/REQ-001/requirements.txt
pytest -q runs/kit/REQ-001/test