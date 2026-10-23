from __future__ import annotations

from importlib import resources

from flask import current_app
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool


def make_pool(database_url: str) -> ConnectionPool:
    return ConnectionPool(
        database_url, min_size=1, max_size=10, timeout=10, kwargs={"row_factory": dict_row}, open=True
    )


def pool() -> ConnectionPool:
    return current_app.extensions["lopper_pool"]


def init_db() -> None:
    """Create the tables if they don't exist yet."""
    schema = resources.files("lopper.api").joinpath("schema.sql").read_text(encoding="utf-8")
    with pool().connection() as conn:
        conn.execute(schema)


def database_is_up() -> bool:
    try:
        with pool().connection(timeout=2) as conn:
            conn.execute("SELECT 1")
        return True
    except Exception:  # noqa: BLE001 - any failure here means "not reachable"
        return False
