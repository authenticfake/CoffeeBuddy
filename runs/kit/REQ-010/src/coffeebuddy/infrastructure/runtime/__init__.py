"""
Runtime integration layer for CoffeeBuddy (REQ-010).

This package exposes:

- Settings: environment-driven configuration for runtime wiring.
- Vault and Ory client abstractions and default HTTP implementations.
- `create_app`: the FastAPI application factory with health and metrics
  endpoints suitable for Kubernetes + Kong deployment.
"""

from .app import create_app, Settings

__all__ = ["create_app", "Settings"]