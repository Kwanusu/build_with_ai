import io
import json
import urllib.error
from urllib.parse import parse_qs, urlsplit

import pytest

from lopper.api import github as github_module
from lopper.api.github import GitHubClient, GitHubError


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def reply(payload):
    return FakeResponse(json.dumps(payload).encode())


@pytest.fixture()
def client():
    return GitHubClient("the-id", "the-secret", "read:user repo")


@pytest.fixture()
def requests_made(monkeypatch):
    """Replace the network. Set `.responses` to a list of payloads (or exceptions), in order."""

    class Recorder:
        responses: list = []
        seen: list = []

    recorder = Recorder()
    recorder.responses = []
    recorder.seen = []

    def fake_urlopen(request, timeout=None):
        recorder.seen.append(request)
        item = recorder.responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return reply(item)

    monkeypatch.setattr(github_module.urllib.request, "urlopen", fake_urlopen)
    return recorder


def test_the_authorize_url_asks_for_the_configured_scopes_and_our_state(client):
    url = urlsplit(client.authorize_url("some-state"))
    query = parse_qs(url.query)
    assert f"{url.scheme}://{url.netloc}{url.path}" == "https://github.com/login/oauth/authorize"
    assert query["client_id"] == ["the-id"] and query["state"] == ["some-state"] and query["scope"] == ["read:user repo"]
    assert "the-secret" not in url.query


def test_exchanging_a_code_sends_the_secret_in_the_body_not_the_url(client, requests_made):
    requests_made.responses = [{"access_token": "gho_new"}]
    assert client.exchange_code("the-code") == "gho_new"
    request = requests_made.seen[0]
    assert request.full_url == "https://github.com/login/oauth/access_token"
    body = parse_qs(request.data.decode())
    assert body == {"client_id": ["the-id"], "client_secret": ["the-secret"], "code": ["the-code"]}
    assert request.get_header("Accept") == "application/json"


def test_a_code_github_rejects_is_a_bad_code(client, requests_made):
    requests_made.responses = [{"error": "bad_verification_code"}]
    with pytest.raises(GitHubError) as error:
        client.exchange_code("old")
    assert error.value.code == "bad_code"


def test_the_profile_is_read_with_the_users_token(client, requests_made):
    requests_made.responses = [{"id": 7, "login": "octo", "avatar_url": "https://a/b.png", "email": "private@example.com"}]
    assert client.get_user("gho_tok") == {"id": 7, "login": "octo", "avatar_url": "https://a/b.png"}
    assert requests_made.seen[0].get_header("Authorization") == "Bearer gho_tok"


def test_an_unexpected_profile_shape_is_an_error(client, requests_made):
    requests_made.responses = [{"message": "hmm"}]
    with pytest.raises(GitHubError) as error:
        client.get_user("t")
    assert error.value.code == "unavailable"


def test_a_401_means_the_token_was_revoked(client, requests_made):
    requests_made.responses = [urllib.error.HTTPError("u", 401, "Unauthorized", {}, None)]
    with pytest.raises(GitHubError) as error:
        client.list_repos("t")
    assert error.value.code == "token_invalid"


@pytest.mark.parametrize(
    "failure", [urllib.error.HTTPError("u", 503, "Unavailable", {}, None), urllib.error.URLError("no route"), TimeoutError()]
)
def test_other_failures_are_unavailable(client, requests_made, failure):
    requests_made.responses = [failure]
    with pytest.raises(GitHubError) as error:
        client.get_user("t")
    assert error.value.code == "unavailable"


def repo(name, **extra):
    return {"full_name": f"octo/{name}", "owner": {"login": "octo"}, "name": name, "private": False, "description": None,
            "language": "Python", "pushed_at": "2026-10-01T00:00:00Z", **extra}


def test_listing_repos_keeps_only_what_we_need_and_skips_archived_ones(client, requests_made):
    requests_made.responses = [[repo("web", private=True), repo("old", archived=True), repo("gone", disabled=True)]]
    repos = client.list_repos("t")
    assert repos == [
        {"full_name": "octo/web", "owner": "octo", "name": "web", "private": True, "description": None, "language": "Python",
         "pushed_at": "2026-10-01T00:00:00Z"}
    ]
    assert "sort=pushed" in requests_made.seen[0].full_url


def test_listing_repos_follows_pages_until_the_limit(client, requests_made):
    requests_made.responses = [[repo(f"a{i}") for i in range(100)], [repo(f"b{i}") for i in range(100)], [repo("c")]]
    repos = client.list_repos("t", limit=150)
    assert len(repos) == 150
    assert len(requests_made.seen) == 2
    requests_made.responses = [[repo(f"a{i}") for i in range(100)], [repo("last")]]
    assert len(client.list_repos("t", limit=300)) == 101
