# HOWTO — REQ-001 Slack Endpoints

## Prerequisites
- Python 3.12
- `pip` with network access to install the dependencies listed in `runs/kit/REQ-001/requirements.txt`
- Local shell with `pytest` execution rights

## Environment Setup
```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r runs/kit/REQ-001/requirements.txt
export PYTHONPATH=.
```

## Running Tests
```bash
pytest -q runs/kit/REQ-001/test
```

## Local Service Wiring
1. Import and mount the router inside the main FastAPI app:
   ```python
   from coffeebuddy.api.slack import SlackConfig, create_slack_router

   slack_router = create_slack_router(config=SlackConfig(signing_secret="..."))
   app.include_router(slack_router)
   ```
2. Provide the real Slack signing secret via Vault / env per runtime standards.
3. Ensure Kong routes `/slack/command` and `/slack/interaction` to the service.

## Enterprise Runner Notes
- Jenkins/Argo: install requirements via `pip install -r runs/kit/REQ-001/requirements.txt` before invoking `pytest`.
- Sonar/Mendix: no direct integration needed for this REQ; reuse existing pipelines once lint/type jobs are defined in later REQs.

## Troubleshooting
- **Signature errors**: verify the signing secret matches the Slack app; mis-matches return HTTP 401.
- **Invalid usage responses**: confirm slash command text follows `pickup=HH:MM` and `note="..."` syntax.
- **Import errors**: ensure `PYTHONPATH=.` so `coffeebuddy` package roots resolve.

KIT Iteration Log
-----------------
- **Targeted REQ-ID(s)**: REQ-001 (next open REQ, implements Slack slash command & interaction endpoints per plan)
- **In Scope**: Slack router, signature verification, command parsing, interaction acknowledgements, correlation-id-aware responses, unit tests/docs/LTC/HOWTO.
- **Out of Scope**: Run persistence, order workflows, Kafka integration, admin/reminder logic (future REQs).
- **How to run tests**: `pytest -q runs/kit/REQ-001/test`
- **Prerequisites**: Python 3.12, pip deps from `runs/kit/REQ-001/requirements.txt`, set `PYTHONPATH=.`
- **Dependencies and mocks**: No external services invoked; tests run against in-process FastAPI app (httpx ASGI transport). Slack/Kong/Vault mocked by design.
- **Product Owner Notes**: Slash command currently posts starter blocks + tracking ID; wired for future run creation once REQ-002 arrives.
- **RAG citations**: PLAN.md (module placement, dependencies), SPEC.md (Slash UX + correlation IDs), REQ-007 exports (observability awareness), REQ-010 FastAPI context (router mounting pattern).

```json
{
  "index": [
    {
      "req": "REQ-001",
      "src": [
        "runs/kit/REQ-001/src/coffeebuddy/api/slack"
      ],
      "tests": [
        "runs/kit/REQ-001/test/api/slack/test_slack_endpoints.py"
      ]
    }
  ]
}