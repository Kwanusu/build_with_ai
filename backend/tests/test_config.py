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
    for name in ("OPEN_ROUTER_API_KEY", "OPENROUTER_API_KEY", "AI_MODEL", "CHATS_PER_MINUTE"):
        monkeypatch.delenv(name, raising=False)
    for name, value in env.items():
        monkeypatch.setenv(name, value)
    config = Config.from_env()
    return config.chat_api_key, config.chat_model, config.chats_per_minute


def test_chat_has_no_key_until_one_is_set_and_uses_a_default_model_and_limit(monkeypatch):
    assert chat_settings(monkeypatch) == (None, "google/gemini-2.5-flash", 10)


def test_the_key_the_model_and_the_limit_come_from_the_environment(monkeypatch):
    assert chat_settings(monkeypatch, OPEN_ROUTER_API_KEY="sk-or-test", AI_MODEL="test/model", CHATS_PER_MINUTE="3") == ("sk-or-test", "test/model", 3)


def test_quotes_and_spaces_around_the_key_and_model_are_dropped(monkeypatch):
    got = chat_settings(monkeypatch, OPEN_ROUTER_API_KEY='  "sk-or-test" ', AI_MODEL=" 'test/model' ")
    assert got[:2] == ("sk-or-test", "test/model")


def test_empty_chat_settings_count_as_not_set(monkeypatch):
    assert chat_settings(monkeypatch, OPEN_ROUTER_API_KEY="", AI_MODEL="  ") == (None, "google/gemini-2.5-flash", 10)


def test_the_banner_names_the_model_when_chat_is_on_and_never_the_key(monkeypatch):
    from lopper.cli import chat_banner

    banner = chat_banner(Config(chat_api_key="sk-or-secret", chat_model="test/model"))
    assert "Chat is on" in banner and "test/model" in banner and "sk-or-secret" not in banner


def test_the_banner_says_what_chat_needs_when_it_is_off():
    from lopper.cli import chat_banner

    assert "Chat is off" in chat_banner(Config()) and "OPEN_ROUTER_API_KEY" in chat_banner(Config())


def test_openrouters_own_spelling_of_the_key_works_too_and_ours_wins_if_both_are_set(monkeypatch):
    assert chat_settings(monkeypatch, OPENROUTER_API_KEY="sk-or-theirs")[0] == "sk-or-theirs"
    assert chat_settings(monkeypatch, OPENROUTER_API_KEY="sk-or-theirs", OPEN_ROUTER_API_KEY="sk-or-ours")[0] == "sk-or-ours"


@pytest.mark.parametrize("bad", ["ten", "0", "-3", "2.5"])
def test_a_bad_chat_limit_stops_the_server_with_a_clear_message_that_doesnt_echo_it(monkeypatch, bad):
    monkeypatch.setenv("CHATS_PER_MINUTE", bad)
    with pytest.raises(RuntimeError, match="CHATS_PER_MINUTE must be a whole number of 1 or more") as problem:
        Config.from_env()
    assert bad not in str(problem.value).replace("1 or more", "")


def test_an_empty_chat_limit_means_the_default(monkeypatch):
    assert chat_settings(monkeypatch, CHATS_PER_MINUTE="  ")[2] == 10


def frontend_config(monkeypatch, **env):
    for name in ("FRONTEND_URL", "PROXY_SECRET"):
        monkeypatch.delenv(name, raising=False)
    for name, value in env.items():
        monkeypatch.setenv(name, value)
    return Config.from_env()


@pytest.mark.parametrize(
    "pasted",
    [
        "https://lopper.example.workers.dev",
        "  https://lopper.example.workers.dev\n",  # the stray space and newline that came with a paste
        "https://lopper.example.workers.dev/",
        '"https://lopper.example.workers.dev"',
        "﻿https://lopper.example.workers.dev",  # an invisible character
        " https://lopper.example.workers.dev/ \r\n",
    ],
)
def test_the_site_address_is_cleaned_so_redirects_and_the_secure_cookie_still_work(monkeypatch, pasted):
    config = frontend_config(monkeypatch, FRONTEND_URL=pasted)
    assert config.frontend_url == "https://lopper.example.workers.dev"
    assert config.cookie_secure is True
    assert config.allowed_origins >= {"https://lopper.example.workers.dev"}


def test_a_dirty_site_address_no_longer_breaks_the_redirect_after_sign_in(monkeypatch, tmp_path):
    """The sign-in routes send the browser back to FRONTEND_URL. A newline in it made that redirect a 500."""
    from dataclasses import replace

    from lopper.api import create_app

    config = replace(frontend_config(monkeypatch, FRONTEND_URL="  https://lopper.example.workers.dev\n"), database=str(tmp_path / "t.db"))
    app = create_app(config)
    try:
        response = app.test_client().get("/api/auth/github/login")  # sign-in isn't set up here, so it sends you back with a reason
        assert response.status_code == 302
        assert response.headers["Location"] == "https://lopper.example.workers.dev/#/auth/error/not_configured"
    finally:
        app.extensions["lopper_pool"].close()


def test_the_forwarders_shared_secret_is_cleaned_so_a_pasted_newline_cant_stop_it_matching(monkeypatch):
    assert frontend_config(monkeypatch, PROXY_SECRET="  s3cret\n").proxy_secret == "s3cret"
    assert frontend_config(monkeypatch, PROXY_SECRET="   ").proxy_secret is None
    assert frontend_config(monkeypatch).proxy_secret is None
