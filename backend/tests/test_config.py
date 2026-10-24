import pytest

from lopper.api import Config

NAMES = ("CLIENT_ID", "CLIENT_SECRET", "GITHUB_CLIENT_ID", "GITHUB_CLIENT_SECRET", "SECRET_KEY")


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for name in NAMES:
        monkeypatch.delenv(name, raising=False)


def credentials(monkeypatch, **env):
    for name, value in env.items():
        monkeypatch.setenv(name, value)
    config = Config.from_env()
    return config.github_client_id, config.github_client_secret


def test_the_deployed_pair_is_used_when_it_is_the_only_one(monkeypatch):
    assert credentials(monkeypatch, GITHUB_CLIENT_ID="deployed-id", GITHUB_CLIENT_SECRET="deployed-secret") == ("deployed-id", "deployed-secret")


def test_a_local_pair_wins_when_both_are_set(monkeypatch):
    got = credentials(
        monkeypatch, CLIENT_ID="local-id", CLIENT_SECRET="local-secret",
        GITHUB_CLIENT_ID="deployed-id", GITHUB_CLIENT_SECRET="deployed-secret",
    )
    assert got == ("local-id", "local-secret")


def test_a_half_set_local_pair_is_ignored_so_the_two_apps_are_never_mixed(monkeypatch):
    got = credentials(monkeypatch, CLIENT_ID="local-id", GITHUB_CLIENT_ID="deployed-id", GITHUB_CLIENT_SECRET="deployed-secret")
    assert got == ("deployed-id", "deployed-secret")


def test_empty_values_count_as_not_set(monkeypatch):
    got = credentials(monkeypatch, CLIENT_ID="", CLIENT_SECRET="  ", GITHUB_CLIENT_ID="deployed-id", GITHUB_CLIENT_SECRET="deployed-secret")
    assert got == ("deployed-id", "deployed-secret")


def test_sign_in_is_off_with_no_credentials_at_all(monkeypatch):
    assert credentials(monkeypatch) == (None, None)
    assert Config.from_env().auth_enabled is False


def test_the_local_pair_switches_sign_in_on_with_a_secret_key(monkeypatch):
    credentials(monkeypatch, CLIENT_ID="local-id", CLIENT_SECRET="local-secret", SECRET_KEY="k")
    assert Config.from_env().auth_enabled is True
