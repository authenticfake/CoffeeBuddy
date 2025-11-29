# REQ-003 — Run close fairness and summary

## Overview
This slice finalizes the CoffeeBuddy run lifecycle by:
- enforcing authorization before a run is closed,
- selecting a runner via a transparent fairness algorithm that honors recent history,
- transitioning the run to `closed`, snapshotting participant orders, and
- returning a structured summary that the Slack layer can render in channels and DMs.

## Key Modules
| Module | Description |
| --- | --- |
| `coffeebuddy.core.runs` | Orchestrates run close requests, validates actors, snapshots orders, and emits `RunSummary` DTOs. |
| `coffeebuddy.services.fairness` | Provides the runner-selection algorithm and keeps `runner_stats` records updated deterministically. |

Both modules reuse the shared SQLAlchemy models from `coffeebuddy.infra.db`.

## Usage
Typical wiring from the Slack handler:
```python
fairness = FairnessService(session=session)
service = CloseRunService(
    session=session,
    fairness=fairness,
    authorizer=your_authorizer_impl,
)
result = service.close_run(
    CloseRunRequest(
        run_id=payload.run_id,
        actor_user_id=payload.user_id,
        allow_immediate_repeat=payload.allow_repeat,
    )
)
# `result.summary` now contains data for channel + runner DM messages.
```

## Tests
Run slice-scoped tests (with coverage + junit outputs):

```bash
pip install -r runs/kit/REQ-003/requirements.txt
PYTHONPATH=. pytest -q runs/kit/REQ-003/test \
  --junitxml runs/kit/REQ-003/reports/junit.xml \
  --cov=runs/kit/REQ-003/src \
  --cov-report xml:runs/kit/REQ-003/reports/coverage.xml
```

## Notes
- Fairness explains decisions in human-friendly text so Slack payloads can remain transparent.
- Order snapshots set `is_final=True`, ensuring downstream summaries never re-read mutable data.
- The service assumes caller-managed transactions, keeping it composable with existing API middleware.