from __future__ import annotations

from contextlib import contextmanager
from typing import Callable, Iterator

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from .config import DatabaseConfig


def build_engine(config: DatabaseConfig) -> Engine:
    """
    Create a SQLAlchemy Engine configured for Postgres + psycopg.
    """
    return create_engine(
        config.url,
        pool_size=config.pool_size,
        max_overflow=config.max_overflow,
        pool_timeout=config.pool_timeout,
        echo=config.echo,
        future=True,
    )


def create_session_factory(engine: Engine) -> Callable[[], Session]:
    """
    Return a session factory bound to the provided engine.

    Usage:
        SessionFactory = create_session_factory(engine)
        with SessionFactory() as session:
            ...
    """
    return sessionmaker(bind=engine, expire_on_commit=False, autoflush=False, future=True)


@contextmanager
def session_scope(SessionFactory: Callable[[], Session]) -> Iterator[Session]:
    """
    Convenience context manager wrapping transactional session handling.
    """
    session = SessionFactory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def health_check(engine: Engine) -> bool:
    """
    Execute a lightweight SELECT 1 to verify connectivity.

    Returns:
        True when the query succeeds, False otherwise.
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False