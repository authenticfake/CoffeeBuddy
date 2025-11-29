# HOWTO — REQ-004 (Reminder scheduling and delivery)

## Prerequisites
- Python 3.12
- Ability to create virtual environments and install pip packages.
- Local network access is sufficient; Kafka/Postgres/Slack are mocked in tests.

## Environment Setup
```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r runs/kit/REQ-004/requirements.txt
export PYTHONPATH=.
```

## Running Tests Locally
```bash
pytest -q runs/kit/REQ-004/test
```

## Enterprise Runner (Jenkins/GitLab/Sonar)
1. Ensure the agent uses Python 3.12.
2. Install dependencies: `pip install -r runs/kit/REQ-004/requirements.txt`.
3. Run the same pytest command from repository root.
4. Archive `pytest` output if desired; no additional artifacts are produced.

## Artifacts & Reports
- Tests only; no coverage or lint artifacts are generated in this slice.

## Troubleshooting
- **ImportError (coffeebuddy...):** confirm `PYTHONPATH=.` or run commands from repo root.
- **Missing prometheus_client/pydantic:** ensure requirements were installed.
- **Timezone assertions:** tests expect timezone-aware datetimes; ensure system clock isn’t forcing naive datetimes.