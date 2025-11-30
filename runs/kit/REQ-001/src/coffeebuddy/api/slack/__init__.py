"""
Slack HTTP interface for CoffeeBuddy.

REQ-001 introduces slash command and interaction handlers that verify
Slack signatures, enforce basic syntax, and emit user-facing responses
with correlation IDs for traceability.
"""

from .config import SlackConfig
from .router import create_slack_router

__all__ = ["SlackConfig", "create_slack_router"]