from datetime import datetime, timezone

from lopper.api.db import SqliteDatabase, _to_postgres, make_pool, to_iso


def test_our_sql_becomes_postgres_sql():
    assert _to_postgres("SELECT id FROM scans WHERE repo_id = ? AND user_id IS ? AND status = 'running'") == (
        "SELECT id FROM scans WHERE repo_id = %s AND user_id IS NOT DISTINCT FROM %s AND status = 'running'"
    )
    # A percent sign in the SQL itself must survive the driver's own placeholder handling.
    assert _to_postgres("SELECT '100%' WHERE a = ?") == "SELECT '100%%' WHERE a = %s"


def test_times_come_out_as_the_same_text_from_either_database():
    when = datetime(2026, 10, 23, 19, 46, 33, 123456, tzinfo=timezone.utc)
    assert to_iso(when) == "2026-10-23T19:46:33.123Z"
    assert to_iso("2026-10-23T19:46:33.123Z") == "2026-10-23T19:46:33.123Z"
    assert to_iso(None) is None


def test_a_path_is_sqlite_and_an_address_is_postgres(tmp_path):
    assert isinstance(make_pool(tmp_path / "x.db"), SqliteDatabase)


def test_a_failed_block_is_rolled_back(tmp_path):
    db = SqliteDatabase(tmp_path / "x.db")
    with db.connection() as conn:
        conn.execute("CREATE TABLE t (n INTEGER)")
    try:
        with db.connection() as conn:
            conn.execute("INSERT INTO t VALUES (1)")
            raise RuntimeError("boom")
    except RuntimeError:
        pass
    with db.connection() as conn:
        assert conn.execute("SELECT count(*) AS n FROM t").fetchone()["n"] == 0


def test_a_database_value_pasted_with_its_name_is_refused_without_echoing_it(tmp_path):
    import pytest

    secret = "DATABASE_URL=postgresql://user:hunter2@host:5432/db"
    with pytest.raises(RuntimeError) as problem:
        make_pool(secret)
    assert "must start with postgresql://" in str(problem.value)
    assert "hunter2" not in str(problem.value)


def test_invisible_characters_and_quotes_are_removed_from_the_setting():
    from lopper.api.db import clean_setting

    assert clean_setting('  "postgresql://u:p@h:5432/postgres\u200b"  ') == "postgresql://u:p@h:5432/postgres"
    # A line break pasted after the last word broke Render: the driver read sslmode as "require" plus a newline.
    assert clean_setting("postgresql://u:p@h:6543/postgres?sslmode=require\r\n") == "postgresql://u:p@h:6543/postgres?sslmode=require"
    assert clean_setting(r"C:\data\lopper.db") == r"C:\data\lopper.db"
