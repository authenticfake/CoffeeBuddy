from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Base(DeclarativeBase):
    """Base declarative model."""


def build_session_factory(database_url: str):
    engine = create_engine(
        database_url,
        future=True,
        pool_pre_ping=True,
    )
    return sessionmaker(bind=engine, expire_on_commit=False)


__all__ = ["Base", "build_session_factory"]