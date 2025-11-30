# KIT REQ-003 — Run Close Fairness and Summary

## Scope
Implements the CoffeeBuddy run-close workflow: enforcing authorization, running the fairness algorithm, persisting runner assignment, emitting Kafka events, and creating structured summaries for Slack notifications.

## Key Components
- `coffeebuddy.services.fairness`
  - `FairnessSelector`: deterministic runner selection using recent channel history.
- `coffeebuddy.core.runs.service.CloseRunService`
  - Orchestrates close → assign → summarize → publish pipeline.
- `coffeebuddy.core.runs.summary.RunSummaryBuilder`
  - Produces immutable summaries for Slack messages and audits.
- Domain models/exceptions for clarity and testability.

## Testing
`pytest -q runs/kit/REQ-003/test`

Covers fairness selection edge cases and the happy-path run closure, including persistence & event emission.

## Notes
- Reuses shared ORM models (REQ-006) and Kafka abstractions (REQ-007).
- Designed for extension (e.g., injecting richer authorizers or Slack dispatchers) without refactors.