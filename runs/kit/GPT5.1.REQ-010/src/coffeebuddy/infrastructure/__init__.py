"""
Infrastructure layer for CoffeeBuddy.

REQ-010 introduces the `runtime` module, which is responsible for
Kubernetes-facing runtime behavior: ASGI app wiring, health endpoints,
and hooks to platform services like Vault, Ory, and Prometheus.
"""