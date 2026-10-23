import os
from contextlib import contextmanager
from pathlib import Path

import psycopg
import pytest

from lopper.api import Config, create_app
from lopper.api.auth import SESSION_COOKIE, create_session

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


class FakeGitHub:
    """Stands in for GitHub: no network, and it remembers what it was asked."""

    def __init__(self):
        self.user = {"id": 4242, "login": "octo", "avatar_url": "https://avatars.example/octo.png"}
        self.repos = [
            {"full_name": "octo/web", "owner": "octo", "name": "web", "private": True, "description": "Web", "language": "TypeScript", "pushed_at": "2026-10-20T10:00:00Z"},
            {"full_name": "octo/api", "owner": "octo", "name": "api", "private": False, "description": None, "language": "Python", "pushed_at": "2026-10-01T10:00:00Z"},
        ]
        self.exchange_error = None
        self.user_error = None
        self.repos_error = None
        self.codes = []
        self.tokens_used = []

    def authorize_url(self, state):
        return f"https://github.test/authorize?client_id=id&state={state}"

    def exchange_code(self, code):
        self.codes.append(code)
        if self.exchange_error:
            raise self.exchange_error
        return f"gho_secret_token_for_{code}"

    def get_user(self, token):
        self.tokens_used.append(token)
        if self.user_error:
            raise self.user_error
        return self.user

    def list_repos(self, token, limit=300):
        self.tokens_used.append(token)
        if self.repos_error:
            raise self.repos_error
        return self.repos


@pytest.fixture()
def github():
    return FakeGitHub()


@pytest.fixture()
def fetched():
    """Every (repo url, token) the scanner was asked to fetch."""
    return []


@pytest.fixture()
def fake_fetch(project, fetched):
    @contextmanager
    def fetch(ref, token=None):
        fetched.append((ref.url, token))
        yield project

    return fetch


@pytest.fixture()
def make_app(fake_fetch):
    created = []

    def build(fetch=None, github=None, **config):
        if github is not None:
            config.setdefault("github_client_id", "client-id")
            config.setdefault("github_client_secret", "client-secret")
            config.setdefault("secret_key", "test-secret-key")
        app = create_app(
            Config(database_url=TEST_DATABASE_URL, scan_inline=config.pop("scan_inline", True), **config),
            fetch=fetch or fake_fetch,
            github=github,
        )
        with app.extensions["lopper_pool"].connection() as conn:
            conn.execute("TRUNCATE users, repos RESTART IDENTITY CASCADE")
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


@pytest.fixture()
def auth_app(make_app, github):
    """An app with GitHub sign-in switched on, using the fake GitHub."""
    return make_app(github=github)


def sign_in(app, github_id=4242, login="octo", token="gho_existing_token"):
    """Create a user and a session directly, and return a test client that has the session cookie."""
    pool = app.extensions["lopper_pool"]
    encrypted = app.extensions["lopper_tokens"].encrypt(token)
    with pool.connection() as conn:
        user = conn.execute(
            """INSERT INTO users (github_id, login, avatar_url, access_token_encrypted) VALUES (%s, %s, %s, %s)
               ON CONFLICT (github_id) DO UPDATE SET login = EXCLUDED.login RETURNING id""",
            (github_id, login, f"https://avatars.example/{login}.png", encrypted),
        ).fetchone()
    cookie = create_session(pool, user["id"], 30)
    client = app.test_client()
    client.set_cookie(SESSION_COOKIE, cookie)
    return client, user["id"]
