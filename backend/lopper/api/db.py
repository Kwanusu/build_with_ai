"""Storage: SQLite for development, Postgres (for example Supabase) in production.

`DATABASE_URL` picks one. A `postgres://` or `postgresql://` address uses Postgres, anything else is a SQLite file path.
The rest of the app writes one kind of SQL: `?` for parameters, and `IS ?` to compare with a value that may be NULL.
Each `connection()` is one short transaction, committed when the block ends and rolled back if it raises.

SQLite keeps times as UTC text in one fixed format (`2026-10-23T19:46:33.123Z`) and booleans as 0/1.
Postgres uses real timestamps and booleans. `to_iso` turns either kind of time into the text the API returns.
"""

from __future__ import annotations

import re
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timezone
from importlib import resources
from pathlib import Path

from flask import current_app

IS_POSTGRES = re.compile(r"^postgres(ql)?://", re.IGNORECASE)

try:  # Postgres support is optional: `pip install "lopper[postgres]"`
    import psycopg
    from psycopg.rows import dict_row
    from psycopg_pool import ConnectionPool

    INTEGRITY_ERRORS: tuple[type[Exception], ...] = (sqlite3.IntegrityError, psycopg.errors.IntegrityError)
except ImportError:  # pragma: no cover - exercised only where psycopg isn't installed
    psycopg = None
    INTEGRITY_ERRORS = (sqlite3.IntegrityError,)


def format_time(value: datetime) -> str:
    value = value.astimezone(timezone.utc) if value.tzinfo else value.replace(tzinfo=timezone.utc)
    return value.strftime(f"%Y-%m-%dT%H:%M:%S.{value.microsecond // 1000:03d}Z")


def to_iso(value: datetime | str | None) -> str | None:
    """A time from either database as the text the API returns."""
    if value is None or isinstance(value, str):
        return value
    return format_time(value)


def _now() -> str:
    return format_time(datetime.now(timezone.utc))


sqlite3.register_adapter(datetime, format_time)


def _dict_row(cursor: sqlite3.Cursor, row: tuple) -> dict:
    return {column[0]: value for column, value in zip(cursor.description, row)}


class SqliteDatabase:
    """A SQLite file. The folder is created if it doesn't exist."""

    kind = "sqlite"

    def __init__(self, path: str | Path, timeout: float = 10) -> None:
        self.path = Path(path)
        self.timeout = timeout
        self.path.parent.mkdir(parents=True, exist_ok=True)
        conn = self._open()
        try:
            conn.execute("PRAGMA journal_mode = WAL")  # readers don't block the writer
        finally:
            conn.close()

    def _open(self, timeout: float | None = None) -> sqlite3.Connection:
        # isolation_level=None: we begin and end transactions ourselves, below.
        conn = sqlite3.connect(self.path, timeout=timeout or self.timeout, isolation_level=None)
        conn.row_factory = _dict_row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.create_function("now", 0, _now)
        return conn

    @contextmanager
    def connection(self, timeout: float | None = None, write: bool = False) -> Iterator[sqlite3.Connection]:
        """Pass `write=True` when the block reads and then writes, so it takes the write lock up front
        instead of failing later because another writer got in between."""
        conn = self._open(timeout)
        try:
            conn.execute("BEGIN IMMEDIATE" if write else "BEGIN")
            yield conn
            conn.execute("COMMIT")
        except BaseException:
            if conn.in_transaction:
                conn.execute("ROLLBACK")
            raise
        finally:
            conn.close()

    def run_script(self, script: str) -> None:
        conn = self._open()
        try:
            conn.executescript(script)
        finally:
            conn.close()

    def close(self) -> None:
        """Nothing stays open between calls."""


def _to_postgres(sql: str) -> str:
    """Our SQL dialect to Postgres: `?` becomes `%s`, and `IS ?` (NULL-safe equality) becomes IS NOT DISTINCT FROM."""
    sql = sql.replace("%", "%%")
    sql = re.sub(r"\bIS \?", "IS NOT DISTINCT FROM ?", sql)
    return sql.replace("?", "%s")


class _PostgresConnection:
    def __init__(self, conn) -> None:
        self._conn = conn

    def execute(self, sql: str, params=()):
        return self._conn.execute(_to_postgres(sql), params)

    def executemany(self, sql: str, rows) -> None:
        with self._conn.cursor() as cursor:
            cursor.executemany(_to_postgres(sql), rows)


class PostgresDatabase:
    kind = "postgres"

    def __init__(self, url: str, max_size: int = 10) -> None:
        if psycopg is None:
            raise RuntimeError('Postgres needs the psycopg package. Install it with: pip install "lopper[postgres]"')
        # prepare_threshold=None: Supabase's pooled connections (port 6543) don't support prepared statements.
        self.pool = ConnectionPool(
            url, min_size=1, max_size=max_size, timeout=10, open=True,
            kwargs={"row_factory": dict_row, "prepare_threshold": None},
        )

    @contextmanager
    def connection(self, timeout: float | None = None, write: bool = False) -> Iterator[_PostgresConnection]:
        with self.pool.connection(timeout=timeout) as conn:
            yield _PostgresConnection(conn)

    def run_script(self, script: str) -> None:
        with self.pool.connection() as conn:
            conn.execute(script)

    def close(self) -> None:
        self.pool.close()


Database = SqliteDatabase | PostgresDatabase


# Characters that are invisible but get copied along with an address from a web page.
INVISIBLE = dict.fromkeys(map(ord, "​‌‍⁠﻿ "))


def clean_setting(value: str | Path) -> str:
    """The setting without stray spaces, quotes or invisible characters."""
    return str(value).translate(INVISIBLE).strip().strip("\"'").strip()


def make_pool(database: str | Path) -> Database:
    database = clean_setting(database)
    if IS_POSTGRES.match(database):
        return PostgresDatabase(database)
    if "://" in database:
        # Not echoed back: it may hold a password.
        raise RuntimeError(
            "DATABASE_URL must start with postgresql:// (or be the path of a SQLite file). It doesn't. "
            "Check that the value doesn't include the name, like DATABASE_URL=, at the start."
        )
    return SqliteDatabase(database)


def pool() -> Database:
    return current_app.extensions["lopper_pool"]


def init_db() -> None:
    """Create the tables if they don't exist yet."""
    db = pool()
    name = "schema.postgres.sql" if db.kind == "postgres" else "schema.sql"
    db.run_script(resources.files("lopper.api").joinpath(name).read_text(encoding="utf-8"))


def database_is_up() -> bool:
    try:
        with pool().connection(timeout=2) as conn:
            conn.execute("SELECT 1")
        return True
    except Exception:  # noqa: BLE001 - any failure here means "not reachable"
        return False
