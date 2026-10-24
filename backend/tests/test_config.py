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


def test_the_chosen_app_is_named_and_the_banner_says_which_callback_to_register(monkeypatch):
    from lopper.cli import sign_in_banner

    credentials(monkeypatch, CLIENT_ID="local-id", CLIENT_SECRET="local-secret", GITHUB_CLIENT_ID="deployed-id",
                GITHUB_CLIENT_SECRET="deployed-secret", SECRET_KEY="k")
    config = Config.from_env()
    assert config.github_app == "local"
    banner = sign_in_banner(config)
    assert "local OAuth app (Client ID local-id)" in banner
    assert "http://localhost:5173/api/auth/github/callback" in banner
    assert "local-secret" not in banner and "deployed-secret" not in banner


def test_the_banner_says_when_sign_in_is_off(monkeypatch):
    from lopper.cli import sign_in_banner

    credentials(monkeypatch)
    assert "sign-in is off" in sign_in_banner(Config.from_env())


def chat_settings(monkeypatch, **env):
    for name in ("GEMINI_API_KEY", "AI_MODEL", "CHATS_PER_MINUTE"):
        monkeypatch.delenv(name, raising=False)
    for name, value in env.items():
        monkeypatch.setenv(name, value)
    config = Config.from_env()
    return config.gemini_api_key, config.chat_model, config.chats_per_minute


def test_chat_has_no_key_until_one_is_set_and_uses_a_default_model_and_limit(monkeypatch):
    assert chat_settings(monkeypatch) == (None, "gemini-flash-latest", 10)


def test_the_key_the_model_and_the_limit_come_from_the_environment(monkeypatch):
    assert chat_settings(monkeypatch, GEMINI_API_KEY="AIza-test", AI_MODEL="gemini-test", CHATS_PER_MINUTE="3") == ("AIza-test", "gemini-test", 3)


def test_quotes_and_spaces_around_the_key_and_model_are_dropped(monkeypatch):
    got = chat_settings(monkeypatch, GEMINI_API_KEY='  "AIza-test" ', AI_MODEL=" 'gemini-test' ")
    assert got[:2] == ("AIza-test", "gemini-test")


def test_empty_chat_settings_count_as_not_set(monkeypatch):
    assert chat_settings(monkeypatch, GEMINI_API_KEY="", AI_MODEL="  ") == (None, "gemini-flash-latest", 10)


def test_the_banner_names_the_model_when_chat_is_on_and_never_the_key(monkeypatch):
    from lopper.cli import chat_banner

    banner = chat_banner(Config(gemini_api_key="AIza-secret", chat_model="gemini-test"))
    assert "Chat is on" in banner and "gemini-test" in banner and "AIza-secret" not in banner


def test_the_banner_says_what_chat_needs_when_it_is_off():
    from lopper.cli import chat_banner

    assert "Chat is off" in chat_banner(Config()) and "GEMINI_API_KEY" in chat_banner(Config())
