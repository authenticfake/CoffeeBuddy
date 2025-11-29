# KIT — REQ-002 (Order capture and preference reuse)

## Summary
- Added the `coffeebuddy.core.orders` slice with composable services, repositories, and validators to manage order submission, edits, cancellations, and preference reuse while aligning with the shared ORM models from REQ-006.
- Implemented `coffeebuddy.services.preferences.PreferenceService` to keep user/channel preference snapshots consistent and track reuse metadata.
- Exposed deterministic dataclasses to feed Slack handlers with participant counts and provenance hints, ensuring downstream message builders can stay stateless.

## Testing
- `pytest -q runs/kit/REQ-002/test`