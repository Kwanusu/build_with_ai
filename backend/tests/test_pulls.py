import pytest

from lopper.api.github import GitHubClient, GitHubError

from .conftest import sign_in

REPO = {"repo_url": "https://github.com/acme/web-platform"}


def scan_while_signed_in(auth_app):
    client, user_id = sign_in(auth_app)
    scan = client.post("/api/scans", json=REPO).get_json()["scan"]
    return client, scan


def open_pr(client, scan):
    return client.post(f"/api/scans/{scan['id']}/pull-request")


def test_ticked_items_become_a_pull_request_on_a_new_branch(auth_app, github):
    client, scan = scan_while_signed_in(auth_app)
    response = open_pr(client, scan)
    assert response.status_code == 201
    body = response.get_json()
    assert body["pull_request"]["url"] == "https://github.com/acme/web-platform/pull/7"
    assert body["pull_request"]["base"] == "main"

    (created,) = github.created
    assert created["owner"] == "acme" and created["name"] == "web-platform"
    # Never the default branch: always a new one.
    assert created["branch"].startswith("lopper/remove-unused-") and created["branch"] != created["base"] == "main"
    # The safe items start ticked: left-pad goes and `dead` stops being exported. prettier "needs a closer look", so it
    # starts unticked and stays. Only edited files are sent.
    assert set(created["files"]) == {"package.json", "src/a.ts"}
    assert "left-pad" not in created["files"]["package.json"] and "prettier" in created["files"]["package.json"]
    assert created["files"]["src/a.ts"] == "import { z } from './z';\nfunction dead() {}\n"
    assert "Lock files aren't updated" in created["body"]
    assert {a["item"] for a in body["applied"]} == {"left-pad", "dead"}


def test_only_what_is_ticked_goes_in_the_pull_request(auth_app, github):
    client, scan = scan_while_signed_in(auth_app)
    for finding in scan["findings"]:
        if finding["item"] != "dead":
            client.patch(f"/api/findings/{finding['id']}", json={"ticked": False})
    assert open_pr(client, scan).status_code == 201
    assert set(github.created[0]["files"]) == {"src/a.ts"}


def test_nothing_ticked_asks_for_a_tick_and_changes_nothing(auth_app, github):
    client, scan = scan_while_signed_in(auth_app)
    for finding in scan["findings"]:
        if finding["ticked"]:
            client.patch(f"/api/findings/{finding['id']}", json={"ticked": False})
    response = open_pr(client, scan)
    assert response.status_code == 400 and response.get_json()["code"] == "nothing_ticked"
    assert github.created == []


def test_a_public_scan_cannot_open_a_pull_request(auth_app, github):
    scan = auth_app.test_client().post("/api/scans", json=REPO).get_json()["scan"]
    signed_in, _ = sign_in(auth_app)
    assert open_pr(signed_in, scan).status_code == 403
    assert github.created == []
    assert open_pr(auth_app.test_client(), scan).status_code == 401


def test_someone_elses_private_scan_is_not_found(auth_app, github):
    client, scan = scan_while_signed_in(auth_app)
    other, _ = sign_in(auth_app, github_id=999, login="mallory", token="gho_other")
    assert open_pr(other, scan).status_code == 404
    assert github.created == []


def test_no_write_access_is_explained(auth_app, github):
    client, scan = scan_while_signed_in(auth_app)
    github.can_push = False
    response = open_pr(client, scan)
    assert response.status_code == 403 and response.get_json()["code"] == "no_write_access"
    assert "acme/web-platform" in response.get_json()["error"] and github.created == []


def test_when_none_of_the_ticked_changes_can_be_made_it_says_so_and_lists_them(auth_app, github):
    client, scan = scan_while_signed_in(auth_app)
    github.files = {}  # the files moved or were deleted since the scan
    response = open_pr(client, scan)
    body = response.get_json()
    assert response.status_code == 422 and body["code"] == "nothing_to_change"
    assert {s["item"] for s in body["skipped"]} == {"left-pad", "dead"}
    assert github.created == []


def test_a_package_json_that_moved_on_is_left_out_but_the_rest_still_goes_ahead(auth_app, github):
    client, scan = scan_while_signed_in(auth_app)
    github.files["package.json"] = '{\n  "name": "demo",\n  "private": true,\n    "left-pad": "1",\n    "prettier": "3"\n}\n'
    body = open_pr(client, scan).get_json()
    assert {a["item"] for a in body["applied"]} == {"dead"}
    assert {s["item"] for s in body["skipped"]} == {"left-pad"}
    assert "## Left for you" in github.created[0]["body"]


@pytest.mark.parametrize(
    "code, status, api_code",
    [
        ("forbidden", 403, "github_forbidden"),
        ("not_found", 404, "github_not_found"),
        ("conflict", 409, "github_conflict"),
        ("unavailable", 502, "github_unavailable"),
    ],
)
def test_github_failures_are_explained_without_passing_on_what_github_said(auth_app, github, code, status, api_code):
    client, scan = scan_while_signed_in(auth_app)
    github.pull_error = GitHubError(code, "raw detail with gho_secret_token")
    response = open_pr(client, scan)
    assert response.status_code == status and response.get_json()["code"] == api_code
    assert "gho_" not in response.get_data(as_text=True) and "Nothing has been changed" in response.get_json()["error"]


def test_a_revoked_token_signs_you_out(auth_app, github):
    client, scan = scan_while_signed_in(auth_app)
    github.pull_error = GitHubError("token_invalid", "no")
    response = open_pr(client, scan)
    assert response.status_code == 401 and response.get_json()["code"] == "sign_in_required"
    assert client.get("/api/auth/me").get_json()["user"] is None


def test_the_github_token_goes_to_github_and_never_into_a_reply(auth_app, github):
    client, scan = scan_while_signed_in(auth_app)
    response = open_pr(client, scan)
    assert "gho_existing_token" in github.tokens_used
    assert "gho_existing_token" not in response.get_data(as_text=True)


# ----- the real client's calls to GitHub -----


class RecordingClient(GitHubClient):
    """The real client with the network replaced by canned answers, so we can check what it asks for and in what order."""

    def __init__(self):
        super().__init__("id", "secret", "repo")
        self.calls = []

    def _rest(self, method, path, token, body=None):
        self.calls.append((method, path, body))
        if path.endswith("/git/ref/heads/main"):
            return {"object": {"sha": "base-sha"}}
        if path.endswith("/git/commits/base-sha"):
            return {"tree": {"sha": "base-tree"}}
        if path.endswith("/git/trees"):
            return {"sha": "new-tree"}
        if path.endswith("/git/commits"):
            return {"sha": "new-commit"}
        if path.endswith("/git/refs"):
            return {}
        if path.endswith("/pulls"):
            return {"html_url": "https://github.com/acme/web/pull/3", "number": 3}
        raise AssertionError(f"unexpected call {method} {path}")


def test_the_client_commits_to_a_new_branch_and_opens_the_pull_request_into_the_default_branch():
    client = RecordingClient()
    pull = client.create_pull_request(
        "tok", "acme", "web", base="main", branch="lopper/x", title="T", body="B", commit_message="M",
        files={"b.txt": "2", "a.txt": "1"},
    )
    assert pull == {"url": "https://github.com/acme/web/pull/3", "number": 3, "branch": "lopper/x"}
    calls = [(m, p.removeprefix("/repos/acme/web")) for m, p, _ in client.calls]
    assert calls == [
        ("GET", "/git/ref/heads/main"),
        ("GET", "/git/commits/base-sha"),
        ("POST", "/git/trees"),
        ("POST", "/git/commits"),
        ("POST", "/git/refs"),
        ("POST", "/pulls"),
    ]
    by_path = {p.removeprefix("/repos/acme/web"): b for _, p, b in client.calls}
    assert by_path["/git/trees"]["base_tree"] == "base-tree"
    assert [e["path"] for e in by_path["/git/trees"]["tree"]] == ["a.txt", "b.txt"]
    assert by_path["/git/commits"]["parents"] == ["base-sha"]
    # The only thing created is the new branch. Nothing moves `main`.
    assert by_path["/git/refs"] == {"ref": "refs/heads/lopper/x", "sha": "new-commit"}
    assert by_path["/pulls"] == {"title": "T", "head": "lopper/x", "base": "main", "body": "B"}
