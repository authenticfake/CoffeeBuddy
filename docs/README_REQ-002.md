# REQ-002 — Order capture and preference reuse

This slice introduces the core order-management capabilities that power Slack interactive flows:

- `coffeebuddy.core.orders` holds validation, repositories, and the `OrderService` used by Slack handlers to place, edit, cancel, or reuse orders.
- `coffeebuddy.services.preferences` centralizes user preference persistence (`user_preferences` table) so all slices share the same logic.

## Key Concepts

| Component | Responsibility |
| --- | --- |
| `OrderValidator` | Enforces non-empty text and max length (default 280 chars) across all entry points. |
| `OrderService` | Coordinates run/user checks, order upsert/cancel, participant counts, and preference updates. |
| `PreferenceService` | Upserts `UserPreference` rows and tracks `last_used_at` timestamps for auditability. |
| `OrderSubmissionResult` | Provides Slack handlers with the latest participant count and provenance to update channel blocks. |

## Usage

```python
from coffeebuddy.core.orders import OrderService, OrderSubmissionRequest

service = OrderService(session)
result = service.submit_order(
    OrderSubmissionRequest(
        run_id=run_id,
        user_id=user_id,
        order_text="Oat cappuccino",
    )
)
print(result.participant_count)  # drive Slack message updates
```

Use `OrderService.use_last_order` to apply a stored preference and `OrderService.cancel_order` to handle withdraw actions.

## Tests

Run the dedicated suite:

```bash
pytest -q runs/kit/REQ-002/test