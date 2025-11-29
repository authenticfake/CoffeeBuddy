from __future__ import annotations

import os
from typing import Iterable, Set

from .exceptions import AdminAuthorizationError
from .models import AdminActor


class SlackAdminAuthorizer:
    """Performs coarse admin validation using Slack roles and allow-lists."""

    def __init__(
        self,
        *,
        allowed_user_ids: Iterable[str] | None = None,
        role_allowlist: Iterable[str] | None = None,
    ) -> None:
        self._allowed_user_ids: Set[str] = {
            user_id.strip()
            for user_id in (allowed_user_ids or [])
            if user_id and user_id.strip()
        }
        self._role_allowlist: Set[str] = {
            role.lower() for role in (role_allowlist or ("admin", "owner"))
        }

    @classmethod
    def from_env(cls) -> "SlackAdminAuthorizer":
        """Builds an authorizer using the COFFEEBUDDY_ADMIN_USER_IDS env var."""
        csv = os.getenv("COFFEEBUDDY_ADMIN_USER_IDS", "")
        allowed = [value.strip() for value in csv.split(",") if value.strip()]
        return cls(allowed_user_ids=allowed)

    def assert_authorized(self, actor: AdminActor) -> None:
        """Raises when the actor is not allowed to use admin capabilities."""
        if self.is_authorized(actor):
            return
        raise AdminAuthorizationError(
            actor.slack_user_id,
            "User lacks required Slack admin role or allow-list membership.",
        )

    def is_authorized(self, actor: AdminActor) -> bool:
        """Boolean form of the authorization check."""
        if actor.slack_user_id in self._allowed_user_ids:
            return True
        role_matches = any(
            role.lower() in self._role_allowlist for role in actor.slack_roles
        )
        return role_matches