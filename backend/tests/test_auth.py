from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qs, urlsplit

import pytest

from lopper.api.auth import SESSION_COOKIE, STATE_COOKIE, TokenBox, hash_token, new_state, state_matches
from lopper.api.github import GitHubError

from .conftest import sign_in

FRONTEND = "http://localhost:5173"
REPO = {"repo_url": "https://github.com/acme/web-platform"}


def cookie_value(client, name):
    cookie = client.get_cookie(name)
    return cookie.value if cookie else None


def begin_sign_in(client):
    """Visit the login route like a browser would. Returns the state GitHub would send back."""
    response = client.get("/api/auth/github/login")
    assert response.status_code == 302
    return parse_qs(urlsplit(response.headers["Location"]).query)["state"][0]


def sign_in_through_github(client, code="abc"):
    state = begin_sign_in(client)
    return client.get(f"/api/auth/github/callback?code={code}&state={state}")


# ---------- helpers ----------


def test_tokens_are_encrypted_and_only_the_right_key_reads_them():
    box = TokenBox("one-secret")
    encrypted = box.encrypt("gho_abc123")
    assert "gho_abc123" not in encrypted
    assert box.decrypt(encrypted) == "gho_abc123"
    assert TokenBox("another-secret").decrypt(encrypted) is None
    assert box.decrypt("not even encrypted") is None


def test_sign_in_state_is_signed_and_must_match():
    state, signed = new_state("k")
    assert state_matches("k", signed, state)
    assert not state_matches("k", signed, state + "x")
    assert not state_matches("other-key", signed, state)
    assert not state_matches("k", None, state)
    assert not state_matches("k", "tampered" + signed, state)
    assert not state_matches("k", signed, None)


# ---------- who am I ----------


def test_me_when_signed_out(client):
    assert client.get("/api/auth/me").get_json() == {"user": None, "sign_in_available": False, "chat_available": False}


def test_me_says_sign_in_is_available_when_configured(auth_app):
    assert auth_app.test_client().get("/api/auth/me").get_json() == {"user": None, "sign_in_available": True, "chat_available": False}


def test_me_when_signed_in(auth_app):
    client, _ = sign_in(auth_app)
    assert client.get("/api/auth/me").get_json()["user"] == {"login": "octo", "avatar_url": "https://avatars.example/octo.png"}


# ---------- the sign-in handshake ----------


def test_login_goes_to_github_with_a_state_cookie(auth_app):
    client = auth_app.test_client()
    response = client.get("/api/auth/github/login")
    assert response.status_code == 302
    location = urlsplit(response.headers["Location"])
    assert location.netloc == "github.test"
    state = parse_qs(location.query)["state"][0]
    header = next(h for h in response.headers.getlist("Set-Cookie") if h.startswith(STATE_COOKIE))
    assert "HttpOnly" in header and "SameSite=Lax" in header
    assert state_matches("test-secret-key", cookie_value(client, STATE_COOKIE), state)


def test_login_without_a_configured_github_app_goes_back_to_the_site_with_a_reason(client):
    response = client.get("/api/auth/github/login")
    assert response.status_code == 302
    assert response.headers["Location"] == f"{FRONTEND}/#/auth/error/not_configured"


def test_a_successful_sign_in_creates_a_user_and_a_session(auth_app, github):
    client = auth_app.test_client()
    response = sign_in_through_github(client, "good-code")
    assert response.status_code == 302
    assert response.headers["Location"] == f"{FRONTEND}/#/scan"
    assert github.codes == ["good-code"]
    header = next(h for h in response.headers.getlist("Set-Cookie") if h.startswith(SESSION_COOKIE))
    assert "HttpOnly" in header and "SameSite=Lax" in header
    assert client.get("/api/auth/me").get_json()["user"]["login"] == "octo"
    assert cookie_value(client, STATE_COOKIE) is None  # the one-time state is gone


def test_the_github_token_is_stored_encrypted_and_the_session_stored_hashed(auth_app):
    client = auth_app.test_client()
    sign_in_through_github(client, "good-code")
    session = cookie_value(client, SESSION_COOKIE)
    with auth_app.extensions["lopper_pool"].connection() as conn:
        user = conn.execute("SELECT * FROM users").fetchone()
        stored_session = conn.execute("SELECT token_hash FROM sessions").fetchone()
    assert "gho_secret_token_for_good-code" not in user["access_token_encrypted"]
    assert auth_app.extensions["lopper_tokens"].decrypt(user["access_token_encrypted"]) == "gho_secret_token_for_good-code"
    assert stored_session["token_hash"] == hash_token(session) and stored_session["token_hash"] != session


def test_signing_in_again_updates_the_same_user(auth_app, github):
    sign_in_through_github(auth_app.test_client(), "first")
    github.user = {**github.user, "login": "octo-renamed"}
    client = auth_app.test_client()
    sign_in_through_github(client, "second")
    with auth_app.extensions["lopper_pool"].connection() as conn:
        users = conn.execute("SELECT login FROM users").fetchall()
    assert users == [{"login": "octo-renamed"}]
    assert client.get("/api/auth/me").get_json()["user"]["login"] == "octo-renamed"


@pytest.mark.parametrize("query", ["?code=abc&state=forged", "?code=abc", "?state=x", ""])
def test_a_sign_in_with_the_wrong_state_is_refused(auth_app, query):
    client = auth_app.test_client()
    begin_sign_in(client)
    response = client.get(f"/api/auth/github/callback{query}")
    assert response.headers["Location"] == f"{FRONTEND}/#/auth/error/invalid_state"
    assert cookie_value(client, SESSION_COOKIE) is None


def test_a_callback_with_no_state_cookie_is_refused(auth_app):
    response = auth_app.test_client().get("/api/auth/github/callback?code=abc&state=anything")
    assert response.headers["Location"] == f"{FRONTEND}/#/auth/error/invalid_state"


def test_choosing_not_to_sign_in_is_explained_not_treated_as_an_error(auth_app):
    client = auth_app.test_client()
    begin_sign_in(client)
    response = client.get("/api/auth/github/callback?error=access_denied")
    assert response.headers["Location"] == f"{FRONTEND}/#/auth/error/access_denied"


@pytest.mark.parametrize(
    ("error", "reason"),
    [(GitHubError("unavailable", "down"), "github_unavailable"), (GitHubError("bad_code", "no"), "invalid_code")],
)
def test_github_failures_send_you_back_with_a_reason(auth_app, github, error, reason):
    github.exchange_error = error
    response = sign_in_through_github(auth_app.test_client())
    assert response.headers["Location"] == f"{FRONTEND}/#/auth/error/{reason}"


def test_a_failure_fetching_the_profile_creates_no_session(auth_app, github):
    github.user_error = GitHubError("unavailable", "down")
    client = auth_app.test_client()
    sign_in_through_github(client)
    assert cookie_value(client, SESSION_COOKIE) is None
    with auth_app.extensions["lopper_pool"].connection() as conn:
        assert conn.execute("SELECT count(*) AS n FROM users").fetchone()["n"] == 0


def test_signing_out_ends_the_session(auth_app):
    client, _ = sign_in(auth_app)
    assert client.post("/api/auth/logout").get_json() == {"ok": True}
    assert client.get("/api/auth/me").get_json()["user"] is None
    with auth_app.extensions["lopper_pool"].connection() as conn:
        assert conn.execute("SELECT count(*) AS n FROM sessions").fetchone()["n"] == 0


def test_an_expired_session_is_signed_out(auth_app):
    client, _ = sign_in(auth_app)
    with auth_app.extensions["lopper_pool"].connection() as conn:
        conn.execute("UPDATE sessions SET expires_at = ?", (datetime.now(timezone.utc) - timedelta(minutes=1),))
    assert client.get("/api/auth/me").get_json()["user"] is None


def test_a_made_up_session_cookie_is_signed_out(auth_app):
    client = auth_app.test_client()
    client.set_cookie(SESSION_COOKIE, "made-up")
    assert client.get("/api/auth/me").get_json()["user"] is None


# ---------- your repos ----------


def test_listing_repos_needs_sign_in(auth_app):
    response = auth_app.test_client().get("/api/repos")
    assert response.status_code == 401 and response.get_json()["code"] == "sign_in_required"


def test_listing_repos_uses_your_github_token(auth_app, github):
    client, _ = sign_in(auth_app, token="gho_mine")
    response = client.get("/api/repos")
    assert response.status_code == 200
    assert [r["full_name"] for r in response.get_json()["repos"]] == ["octo/web", "octo/api"]
    assert github.tokens_used == ["gho_mine"]
    assert "gho_mine" not in response.get_data(as_text=True)


def test_github_being_down_is_explained(auth_app, github):
    github.repos_error = GitHubError("unavailable", "down")
    client, _ = sign_in(auth_app)
    response = client.get("/api/repos")
    assert response.status_code == 502 and "Nothing has been changed" in response.get_json()["error"]
    assert client.get("/api/auth/me").get_json()["user"] is not None  # still signed in


def test_a_revoked_github_token_signs_you_out_everywhere(auth_app, github):
    github.repos_error = GitHubError("token_invalid", "revoked")
    client, _ = sign_in(auth_app)
    other_device, _ = sign_in(auth_app)
    response = client.get("/api/repos")
    assert response.status_code == 401 and response.get_json()["code"] == "sign_in_required"
    assert other_device.get("/api/auth/me").get_json()["user"] is None


# ---------- who can see and tick which scan ----------


def test_a_signed_in_scan_uses_your_token_and_a_public_scan_uses_none(auth_app, fetched):
    anonymous = auth_app.test_client()
    signed_in, _ = sign_in(auth_app, token="gho_mine")
    anonymous.post("/api/scans", json=REPO)
    signed_in.post("/api/scans", json=REPO)
    assert fetched == [("https://github.com/acme/web-platform", None), ("https://github.com/acme/web-platform", "gho_mine")]


def test_a_scan_made_while_signed_in_is_private_to_you(auth_app):
    owner, _ = sign_in(auth_app, github_id=1, login="owner")
    stranger, _ = sign_in(auth_app, github_id=2, login="stranger")
    anonymous = auth_app.test_client()
    scan_id = owner.post("/api/scans", json=REPO).get_json()["scan"]["id"]
    assert owner.get(f"/api/scans/{scan_id}").status_code == 200
    for viewer in (stranger, anonymous):
        assert viewer.get(f"/api/scans/{scan_id}").status_code == 404
        assert viewer.get("/api/repos/acme/web-platform/scan").status_code == 404


def test_a_public_scan_can_be_read_by_anyone_but_ticked_by_no_one(auth_app):
    anonymous = auth_app.test_client()
    scan = anonymous.post("/api/scans", json=REPO).get_json()["scan"]
    assert scan["can_tick"] is False
    signed_in, _ = sign_in(auth_app)
    seen = signed_in.get(f"/api/scans/{scan['id']}").get_json()["scan"]
    assert seen["can_tick"] is False
    finding_id = scan["findings"][0]["id"]
    assert anonymous.patch(f"/api/findings/{finding_id}", json={"ticked": False}).status_code == 401
    refused = signed_in.patch(f"/api/findings/{finding_id}", json={"ticked": False})
    assert refused.status_code == 403 and refused.get_json()["code"] == "public_scan"
    assert "Rescan while signed in" in refused.get_json()["error"]


def test_only_the_owner_can_tick_a_private_scan(auth_app):
    owner, _ = sign_in(auth_app, github_id=1, login="owner")
    stranger, _ = sign_in(auth_app, github_id=2, login="stranger")
    scan = owner.post("/api/scans", json=REPO).get_json()["scan"]
    assert scan["can_tick"] is True
    finding_id = next(f["id"] for f in scan["findings"] if not f["report_only"])
    assert stranger.patch(f"/api/findings/{finding_id}", json={"ticked": False}).status_code == 404
    assert owner.patch(f"/api/findings/{finding_id}", json={"ticked": False}).status_code == 200


def test_a_public_scan_and_your_own_scan_of_the_same_repo_live_side_by_side(auth_app):
    anonymous = auth_app.test_client()
    signed_in, _ = sign_in(auth_app)
    public_id = anonymous.post("/api/scans", json=REPO).get_json()["scan"]["id"]
    own_id = signed_in.post("/api/scans", json=REPO).get_json()["scan"]["id"]
    assert public_id != own_id
    assert anonymous.get("/api/repos/acme/web-platform/scan").get_json()["scan"]["id"] == public_id
    latest_for_owner = signed_in.get("/api/repos/acme/web-platform/scan").get_json()["scan"]
    assert latest_for_owner["id"] == own_id and latest_for_owner["can_tick"] is True


def test_rescanning_replaces_only_your_own_scan(auth_app):
    anonymous = auth_app.test_client()
    signed_in, _ = sign_in(auth_app)
    public_id = anonymous.post("/api/scans", json=REPO).get_json()["scan"]["id"]
    first = signed_in.post("/api/scans", json=REPO).get_json()["scan"]["id"]
    second = signed_in.post("/api/scans", json=REPO).get_json()["scan"]["id"]
    assert first != second
    assert signed_in.get(f"/api/scans/{first}").status_code == 404
    assert anonymous.get(f"/api/scans/{public_id}").status_code == 200


def test_a_session_whose_token_can_no_longer_be_read_asks_you_to_sign_in_again(auth_app):
    client, user_id = sign_in(auth_app)
    with auth_app.extensions["lopper_pool"].connection() as conn:
        conn.execute("UPDATE users SET access_token_encrypted = 'garbage' WHERE id = ?", (user_id,))
    response = client.post("/api/scans", json=REPO)
    assert response.status_code == 401 and response.get_json()["code"] == "sign_in_required"


# ---------- requests from other sites ----------


def test_a_state_changing_request_from_another_site_is_refused(auth_app):
    client, _ = sign_in(auth_app)
    response = client.post("/api/scans", json=REPO, headers={"Origin": "https://evil.example"})
    assert response.status_code == 403 and response.get_json()["code"] == "bad_origin"
    assert "https://evil.example" in response.get_json()["error"]
    assert client.patch("/api/findings/1", json={"ticked": True}, headers={"Origin": "https://evil.example"}).status_code == 403
    assert client.post("/api/auth/logout", headers={"Origin": "https://evil.example"}).status_code == 403


def test_our_own_site_and_non_browser_clients_are_allowed(auth_app):
    client, _ = sign_in(auth_app)
    assert client.post("/api/scans", json=REPO, headers={"Origin": FRONTEND}).status_code == 202
    assert client.post("/api/scans", json=REPO).status_code in (200, 202)  # no Origin header: curl, the CLI


def test_cors_allows_credentials_for_our_site_only(auth_app):
    allowed = auth_app.test_client().get("/api/auth/me", headers={"Origin": FRONTEND})
    assert allowed.headers["Access-Control-Allow-Origin"] == FRONTEND
    assert allowed.headers["Access-Control-Allow-Credentials"] == "true"
    other = auth_app.test_client().get("/api/auth/me", headers={"Origin": "https://evil.example"})
    assert "Access-Control-Allow-Origin" not in other.headers


def test_the_refusal_names_a_wrong_dev_port_and_says_what_to_do(auth_app):
    response = auth_app.test_client().post("/api/scans", json=REPO, headers={"Origin": "http://localhost:5174"})
    message = response.get_json()["error"]
    assert response.status_code == 403
    assert "http://localhost:5174" in message and "Open the site at http://localhost:5173" in message
    assert "CORS_ORIGINS" in message and "Nothing has been changed" in message


@pytest.mark.parametrize("origin", ["null", "javascript:alert(1)", "http://<script>", "http://" + "a" * 200])
def test_an_odd_origin_is_refused_without_being_echoed(auth_app, origin):
    response = auth_app.test_client().post("/api/scans", json=REPO, headers={"Origin": origin})
    assert response.status_code == 403
    assert origin not in response.get_json()["error"]
