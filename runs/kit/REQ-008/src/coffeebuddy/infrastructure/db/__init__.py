"""
Database infrastructure primitives for CoffeeBuddy.

REQ-008 establishes the canonical SQLAlchemy metadata, connection
configuration, and repository facades that higher-level domains will
compose in later REQs.
"""

from .config import DatabaseConfig
from .models import (
    Base,
    Channel,
    ChannelAdminAction,
    Order,
    RunnerStat,
    Run,
    RunStatus,
    User,
    UserPreference,
)
from .repositories import (
    ChannelAdminActionRepository,
    ChannelRepository,
    ChannelSettingsPatch,
    OrderRepository,
    RunnerStatsRepository,
    RunRepository,
    UserPreferenceRepository,
    UserRepository,
)
from .session import build_engine, create_session_factory, health_check

__all__ = [
    "Base",
    "build_engine",
    "create_session_factory",
    "health_check",
    "DatabaseConfig",
    "RunStatus",
    "User",
    "Channel",
    "Run",
    "Order",
    "UserPreference",
    "RunnerStat",
    "ChannelAdminAction",
    "UserRepository",
    "ChannelRepository",
    "RunRepository",
    "OrderRepository",
    "UserPreferenceRepository",
    "RunnerStatsRepository",
    "ChannelAdminActionRepository",
    "ChannelSettingsPatch",
]