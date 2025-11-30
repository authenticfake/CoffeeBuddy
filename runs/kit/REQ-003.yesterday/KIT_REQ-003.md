# KIT — REQ-003

## Scope
- Implemented run-close orchestration (`coffeebuddy.core.runs`) with DTOs, authorization seam, and transactional updates.
- Added fairness service (`coffeebuddy.services.fairness`) that selects runners per runs-served counts, tie-breakers, and immediate-repeat opt-out.
- Covered behavior with unit tests for fairness logic and run-close service paths (success + error cases).

## Verification
- `PYTHONPATH=. pytest -q runs/kit/REQ-003/test --junitxml runs/kit/REQ-003/reports/junit.xml --cov=runs/kit/REQ-003/src --cov-report xml:runs/kit/REQ-003/reports/coverage.xml`

## Artifacts
- Source: `runs/kit/REQ-003/src/coffeebuddy/core/runs`, `runs/kit/REQ-003/src/coffeebuddy/services/fairness`
- Tests: `runs/kit/REQ-003/test`
- CI contract + HOWTO under `runs/kit/REQ-003/ci`