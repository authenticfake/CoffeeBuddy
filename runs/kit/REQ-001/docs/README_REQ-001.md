# REQ-001 — Slack Endpoints

## Summary
Implements Slack-facing HTTP endpoints for `/coffee` slash commands and interactive callbacks. Requests are authenticated via Slack signature verification, malformed input returns actionable usage hints, and all responses include correlation IDs for traceability.

## Key Files
- `src/coffeebuddy/api/slack/router.py` – FastAPI router with `/slack/command` and `/slack/interaction`.
- `src/coffeebuddy/api/slack/signature.py` – Deduplicated Slack signature verifier.
- `src/coffeebuddy/api/slack/commands.py` – Slash command parsing and response rendering.
- `src/coffeebuddy/api/slack/interactions.py` – Interaction payload parsing and acknowledgement.

## Testing
Run `pytest -q runs/kit/REQ-001/test` to execute the end-to-end HTTP tests.

## Next Steps
- Wire router into the service factory from REQ-010.
- Extend handlers to integrate run creation (REQ-002) and order flows (REQ-003).
- Attach observability middleware and metrics when REQ-007 lands.