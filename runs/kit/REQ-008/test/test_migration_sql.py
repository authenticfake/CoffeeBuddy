from __future__ import annotations

import os
from pathlib import Path

import psycopg
import pytest
import sqlparse

ROOT = Path(__file__).resolve().parents[1]
SQL_DIR = ROOT / "src" / "storage" / "sql"
SEED_FILE = ROOT / "src" / "storage" / "seed" / "seed.sql"


def _execute_sql_file(conn: psycopg.Connection, file_path: Path) -> None:
    statements = [stmt.strip() for stmt in sqlparse.split(file_path.read_text()) if stmt.strip()]
    with conn.cursor() as cur:
        for statement in statements:
            cur.execute(statement)


@pytest.fixture(scope="module")
def pg_conn() -> psycopg.Connection:
    dsn = os.getenv("TEST_DATABASE_URL") or os.getenv("DATABASE_URL")
    if not dsn:
        pytest.skip("TEST_DATABASE_URL (or DATABASE_URL) must be set to run migration tests.")
    conn = psycopg.connect(dsn, autocommit=True)
    yield conn
    conn.close()


def test_migration_round_trip(pg_conn: psycopg.Connection) -> None:
    down = sorted(SQL_DIR.glob("V*.down.sql"))
    up = sorted(SQL_DIR.glob("V*.up.sql"))

    for file in reversed(up):
        _execute_sql_file(pg_conn, file)  # ensure schemas exist for safe drops
    for file in down:
        _execute_sql_file(pg_conn, file)

    for file in up:
        _execute_sql_file(pg_conn, file)
    for file in up:
        _execute_sql_file(pg_conn, file)  # idempotent re-run

    with pg_conn.cursor() as cur:
        cur.execute(
            "SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename IN ('users','channels','runs')"
        )
        tables = {row[0] for row in cur.fetchall()}
    assert tables == {"users", "channels", "runs"}

    for file in down:
        _execute_sql_file(pg_conn, file)

    with pg_conn.cursor() as cur:
        cur.execute(
            "SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename='runs'"
        )
        assert cur.fetchone() is None


def test_seed_is_idempotent(pg_conn: psycopg.Connection) -> None:
    up = sorted(SQL_DIR.glob("V*.up.sql"))
    for file in up:
        _execute_sql_file(pg_conn, file)

    _execute_sql_file(pg_conn, SEED_FILE)
    _execute_sql_file(pg_conn, SEED_FILE)

    with pg_conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM channels")
        count = cur.fetchone()[0]

    assert count >= 10, "Seed should ensure pilot channels exist"

    down = sorted(SQL_DIR.glob("V*.down.sql"))
    for file in down:
        _execute_sql_file(pg_conn, file)