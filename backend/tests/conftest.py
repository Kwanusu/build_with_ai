import os
from contextlib import contextmanager
from pathlib import Path

import psycopg
import pytest

from lopper.api import Config, create_app

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL", "postgresql://lopper@localhost:5544/lopper_test")


def _database_available() -> bool:
    try:
        with psycopg.connect(TEST_DATABASE_URL, connect_timeout=3):
            return True
    except psycopg.Error:
        return False


requires_database = pytest.mark.skipif(
    not _database_available(),
    reason=f"Postgres isn't reachable at {TEST_DATABASE_URL}. Start it (see backend/README.md) or set TEST_DATABASE_URL.",
)


def write_project(root: Path) -> Path:
    """A tiny repo with one of each kind of finding."""
    (root / "src").mkdir(parents=True, exist_ok=True)
    (root / "package.json").write_text(
        '{\n  "name": "demo",\n  "dependencies": {"left-pad": "1"},\n  "devDependencies": {"prettier": "3"}\n}\n'
    )
    (root / "src" / "a.ts").write_text("import { z } from './z';\nexport function dead() {}\n")
    return root


@pytest.fixture()
def project(tmp_path):
    return write_project(tmp_path / "project")


@pytest.fixture()
def fake_fetch(project):
    @contextmanager
    def fetch(ref):
        yield project

    return fetch


@pytest.fixture()
def make_app(fake_fetch):
    created = []

    def build(fetch=None, **config):
        app = create_app(
            Config(database_url=TEST_DATABASE_URL, scan_inline=config.pop("scan_inline", True), **config),
            fetch=fetch or fake_fetch,
        )
        with app.extensions["lopper_pool"].connection() as conn:
            conn.execute("TRUNCATE repos RESTART IDENTITY CASCADE")
        created.append(app)
        return app

    yield build
    for app in created:
        app.extensions["lopper_pool"].close()


@pytest.fixture()
def app(make_app):
    return make_app()


@pytest.fixture()
def client(app):
    return app.test_client()
