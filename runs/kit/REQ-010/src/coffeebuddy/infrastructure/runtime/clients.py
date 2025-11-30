from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable, Optional

import httpx

from .settings import Settings


@runtime_checkable
class VaultClient(Protocol):
    """
    Abstraction for Vault health and secret access.

    Only a health check is required for REQ-010 readiness probing.
    Additional methods can be added in later REQs without breaking
    existing code.
    """

    async def health_check(self) -> bool:
        """
        Return True if Vault is reachable and reports a healthy state.

        Implementations MUST NOT log secrets or tokens.
        """
        ...


@runtime_checkable
class OryClient(Protocol):
    """
    Abstraction for Ory readiness.

    For REQ-010, we only use this for a basic health check. Later REQs
    may extend this with token validation helpers and auth policies.
    """

    async def health_check(self) -> bool:
        """
        Return True if the Ory control plane is reachable and healthy.
        """
        ...


@dataclass
class HttpVaultClient:
    """
    HTTP-based implementation of VaultClient using httpx.

    This client targets the standard Vault health endpoint and returns
    True when Vault reports a healthy status (2xx response codes).

    All configuration is provided via `Settings` and environment.
    """

    base_url: str
    token: Optional[str]

    async def health_check(self) -> bool:
        if not self.base_url:
            # When Vault is not configured, treat as unhealthy for
            # readiness so operators can detect misconfiguration.
            return False

        headers = {}
        if self.token:
            headers["X-Vault-Token"] = self.token

        async with httpx.AsyncClient(base_url=self.base_url, timeout=2.0) as client:
            try:
                resp = await client.get("/v1/sys/health", headers=headers)
            except httpx.HTTPError:
                return False
        # Vault typically returns 200 for healthy, 429/472/473 for
        # standby/recovery states. For pilot we treat only 2xx as fully
        # ready.
        return 200 <= resp.status_code < 300


@dataclass
class HttpOryClient:
    """
    HTTP-based implementation of OryClient using httpx.

    This client calls a generic /health/ready endpoint, which matches
    Ory's typical health API surface.
    """

    base_url: str

    async def health_check(self) -> bool:
        if not self.base_url:
            return False

        async with httpx.AsyncClient(base_url=self.base_url, timeout=2.0) as client:
            try:
                resp = await client.get("/health/ready")
            except httpx.HTTPError:
                return False
        return 200 <= resp.status_code < 300


def build_vault_client(settings: Settings) -> VaultClient:
    """
    Construct the default Vault client from settings.

    This is the production path used by `create_app` when no explicit
    client override is supplied.
    """
    return HttpVaultClient(
        base_url=str(settings.vault_addr) if settings.vault_addr else "",
        token=settings.vault_token,
    )


def build_ory_client(settings: Settings) -> OryClient:
    """
    Construct the default Ory client from settings.
    """
    return HttpOryClient(
        base_url=str(settings.ory_base_url) if settings.ory_base_url else ""
    )