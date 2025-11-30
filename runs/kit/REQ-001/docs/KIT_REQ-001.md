# KIT Notes — REQ-001 (Slack HTTP Endpoints)

## Scope
REQ-001 delivers the first customer-facing HTTP surface for CoffeeBuddy by exposing Slack slash command and interaction endpoints. This KIT focuses on request verification, syntax validation, and user-visible responses while keeping seams open for future run lifecycle integration.

## Design Highlights
- **Router factory (`create_slack_router`)** – Returns a FastAPI router that can be mounted by the application composition layer (REQ-010). Dependencies (clock, logger) are injected for testability and later evolution.
- **Signature verification** – `SlackRequestVerifier` centralizes Slack HMAC validation and replay protection with configurable tolerance.
- **Command handling** – `SlashCommandHandler` parses `/coffee` options (`pickup`, `note`), enforces syntax, and emits block-kit payloads with actionable buttons.
- **Interaction acknowledgement** – `InteractionHandler` parses the Slack `payload` envelope and responds with ephemeral confirmations referencing correlation IDs.
- **Observability glue** – Each response includes a tracking block displaying the correlation ID to users, mirroring what is logged server-side.

## Testing
`runs/kit/REQ-001/test/api/slack/test_slack_endpoints.py` covers:
- Successful slash command execution returning interactive blocks.
- Signature rejection on invalid HMAC.
- Usage guidance for malformed text.
- Interaction acknowledgement flow.

Tests exercise the FastAPI router end-to-end using `httpx.AsyncClient` with `ASGITransport`, satisfying the requirement to avoid network calls.

## Extensibility
- Run lifecycle orchestration (REQ-002) can plug into `SlashCommandHandler` via injected services without altering endpoint contracts.
- Interaction handler currently provides acknowledgements; future order/runner workflows can replace or extend the handler while reusing signature verification and correlation helpers.
- The router factory exposes injection points for observability and metrics once REQ-007 and other REQs introduce richer instrumentation.