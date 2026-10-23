"""SQLite storage. Each `connection()` is its own short transaction on its own connection, so threads never share one.

Times are stored as UTC text in one fixed format (`2026-10-23T19:46:33.123Z`), which sorts and compares correctly.
SQL can call `now()` for the current time in that format.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timezone
from importlib import resources
from pathlib import Path

from flask import current_app

TIME_FORMAT = "%Y-%m-%dT%H:%M:%S.{ms}Z"


def format_time(value: datetime) -> str:
    value = value.astimezone(timezone.utc) if value.tzinfo else value.replace(tzinfo=timezone.utc)
    return value.strftime(TIME_FORMAT.format(ms=f"{value.microsecond // 1000:03d}"))


def _now() -> str:
    return format_time(datetime.now(timezone.utc))


sqlite3.register_adapter(datetime, format_time)


def _dict_row(cursor: sqlite3.Cursor, row: tuple) -> dict:
    return {column[0]: value for column, value in zip(cursor.description, row)}


class Database:
    """A SQLite file. `path` is a file path; the folder is created if it doesn't exist."""

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
        """A transaction: committed when the block ends, rolled back if it raises.

        Pass `write=True` when the block reads and then writes, so it takes the write lock up front
        instead of failing later because another writer got in between.
        """
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

    def close(self) -> None:
        """Nothing stays open between calls, so there is nothing to close. Kept so callers can treat it like a pool."""


def make_pool(path: str | Path) -> Database:
    return Database(path)


def pool() -> Database:
    return current_app.extensions["lopper_pool"]


def init_db() -> None:
    """Create the tables if they don't exist yet."""
    schema = resources.files("lopper.api").joinpath("schema.sql").read_text(encoding="utf-8")
    conn = pool()._open()
    try:
        conn.executescript(schema)
    finally:
        conn.close()


def database_is_up() -> bool:
    try:
        with pool().connection(timeout=2) as conn:
            conn.execute("SELECT 1")
        return True
    except Exception:  # noqa: BLE001 - any failure here means "not reachable"
        return False
