from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable

import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine

try:
    from testcontainers.postgres import PostgresContainer
except ImportError:  # pragma: no cover
    PostgresContainer = None

ROOT = Path(__file__).resolve().parents[1]
SQL_PATH = ROOT / "src" / "storage" / "sql"
SEED_PATH = ROOT / "src" / "storage" / "seed" / "seed.sql"


def _load_sql_statements(sql_file: Path) -> Iterable[str]:
    statement = ""
    with sql_file.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped or stripped.startswith("--"):
                continue
            statement += line
            if stripped.endswith(";"):
                yield statement.strip()
                statement = ""
    if statement:
        yield statement.strip()


@pytest.fixture(scope="session")
def engine() -> Engine:
    if PostgresContainer is None:
        pytest.skip("testcontainers is required for migration tests")
    container = PostgresContainer("postgres:16-alpine")
    container.start()
    url = container.get_connection_url().replace("postgresql://", "postgresql+psycopg://", 1)
    engine = create_engine(url, future=True)
    yield engine
    engine.dispose()
    container.stop()


def _run_sql(engine: Engine, sql_file: Path) -> None:
    with engine.begin() as conn:
        for statement in _load_sql_statements(sql_file):
            conn.execute(text(statement))


def _apply_up(engine: Engine) -> None:
    for sql in sorted(SQL_PATH.glob("*.up.sql")):
        _run_sql(engine, sql)


def _apply_down(engine: Engine) -> None:
    for sql in sorted(SQL_PATH.glob("*.down.sql"), reverse=True):
        _run_sql(engine, sql)


def _run_seed(engine: Engine) -> None:
    _run_sql(engine, SEED_PATH)


def test_migrations_create_expected_tables(engine: Engine) -> None:
    _apply_up(engine)
    inspector = inspect(engine)
    expected_tables = {
        "users",
        "channels",
        "runs",
        "orders",
        "user_preferences",
        "runner_stats",
        "channel_admin_actions",
    }
    assert expected_tables.issubset(set(inspector.get_table_names()))

    with engine.connect() as conn:
        retention_default = conn.execute(
            text(
                """
                SELECT column_default
                FROM information_schema.columns
                WHERE table_name='channels'
                  AND column_name='data_retention_days'
                """
            )
        ).scalar_one()
        assert "90" in retention_default

        constraint_check = conn.execute(
            text(
                """
                SELECT conname
                FROM pg_constraint
                WHERE conname='chk_run_status'
                """
            )
        ).scalar_one_or_none()
        assert constraint_check == "chk_run_status"


def test_seed_file_is_idempotent(engine: Engine) -> None:
    _apply_up(engine)
    _run_seed(engine)
    _run_seed(engine)
    with engine.connect() as conn:
        count = conn.execute(
            text("SELECT COUNT(*) FROM channels WHERE slack_channel_id LIKE 'CFOCUS%'")
        ).scalar_one()
        assert count == 10


def test_down_and_reapply(engine: Engine) -> None:
    _apply_up(engine)
    _apply_down(engine)
    inspector = inspect(engine)
    assert "users" not in inspector.get_table_names()

    _apply_up(engine)
    inspector = inspect(engine)
    assert "users" in inspector.get_table_names()