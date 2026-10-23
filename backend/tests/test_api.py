import time
from contextlib import contextmanager

import psycopg
import pytest

from lopper.repo import RepoError

from .conftest import requires_database

pytestmark = requires_database

REPO = {"repo_url": "https://github.com/acme/web-platform"}


def post_scan(client, body=None):
    return client.post("/api/scans", json=body or REPO)


def test_health_reports_the_database(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok", "database": True}


@pytest.mark.parametrize("body", [None, {}, {"repo_url": 5}, {"url": "https://github.com/a/b"}, []])
def test_scan_needs_a_repo_url(client, body):
    response = client.post("/api/scans", json=body)
    assert response.status_code == 400
    assert response.get_json()["code"] == "invalid_request"


@pytest.mark.parametrize("url", ["https://gitlab.com/a/b", "http://github.com/a/b", "not a url", "https://127.0.0.1/a/b"])
def test_scan_rejects_anything_but_a_github_repo(client, url):
    response = post_scan(client, {"repo_url": url})
    assert response.status_code == 400
    assert response.get_json()["code"] == "invalid_repo_url"
    assert "GitHub repo URL" in response.get_json()["error"]


def test_scan_runs_and_stores_findings_with_evidence(client):
    response = post_scan(client)
    assert response.status_code == 202
    scan = response.get_json()["scan"]
    assert scan["status"] == "done" and scan["error"] is None
    assert scan["repo"] == {"url": "https://github.com/acme/web-platform", "owner": "acme", "name": "web-platform"}
    assert scan["files_scanned"] == 1 and scan["packages_scanned"] == 1 and scan["languages"] == ["javascript"]
    assert scan["counts"] == {"unused-package": 1, "unused-dev-dependency": 1, "unused-export": 1, "lint-issue": 1}

    by_type = {f["type"]: f for f in scan["findings"]}
    package = by_type["unused-package"]
    assert package["item"] == "left-pad" and package["file_path"] == "package.json" and package["line"] == 3
    assert "No file under the repo root imports 'left-pad'" in package["evidence"]
    assert package["confidence"] == "safe" and package["ticked"] is True
    assert by_type["unused-dev-dependency"]["confidence"] == "uncertain"
    assert by_type["unused-dev-dependency"]["ticked"] is False  # uncertain starts unticked
    assert by_type["lint-issue"]["report_only"] is True and by_type["lint-issue"]["ticked"] is False


def test_get_scan_returns_the_same_scan_and_can_filter(client):
    scan_id = post_scan(client).get_json()["scan"]["id"]
    full = client.get(f"/api/scans/{scan_id}").get_json()["scan"]
    assert len(full["findings"]) == 4
    only_exports = client.get(f"/api/scans/{scan_id}?type=unused-export").get_json()["scan"]
    assert [f["item"] for f in only_exports["findings"]] == ["dead"]
    assert only_exports["counts"]["unused-package"] == 1  # counts always describe the whole scan
    assert client.get(f"/api/scans/{scan_id}?type=nonsense").status_code == 400


def test_unknown_scan_and_unknown_route_explain_themselves(client):
    missing = client.get("/api/scans/999")
    assert missing.status_code == 404 and missing.get_json()["code"] == "not_found"
    assert client.get("/api/nothing").status_code == 404
    assert client.delete("/api/scans/1").status_code == 405


def test_rescanning_replaces_the_previous_scan(client, app):
    first = post_scan(client).get_json()["scan"]
    second = post_scan(client).get_json()["scan"]
    assert second["id"] != first["id"]
    assert client.get(f"/api/scans/{first['id']}").status_code == 404
    with app.extensions["lopper_pool"].connection() as conn:
        assert conn.execute("SELECT count(*) AS n FROM scans").fetchone()["n"] == 1
        assert conn.execute("SELECT count(*) AS n FROM findings").fetchone()["n"] == 4  # not 8


def test_latest_scan_for_a_repo(client):
    assert client.get("/api/repos/acme/web-platform/scan").status_code == 404
    scan_id = post_scan(client).get_json()["scan"]["id"]
    latest = client.get("/api/repos/acme/web-platform/scan")
    assert latest.status_code == 200 and latest.get_json()["scan"]["id"] == scan_id
    assert client.get("/api/repos/acme/bad name/scan").status_code == 400


def test_ticking_a_finding(client):
    findings = post_scan(client).get_json()["scan"]["findings"]
    uncertain = next(f for f in findings if f["confidence"] == "uncertain" and not f["report_only"])
    response = client.patch(f"/api/findings/{uncertain['id']}", json={"ticked": True})
    assert response.status_code == 200 and response.get_json()["finding"]["ticked"] is True
    again = client.patch(f"/api/findings/{uncertain['id']}", json={"ticked": False})
    assert again.get_json()["finding"]["ticked"] is False


def test_lint_issues_cannot_be_ticked(client):
    findings = post_scan(client).get_json()["scan"]["findings"]
    lint = next(f for f in findings if f["type"] == "lint-issue")
    response = client.patch(f"/api/findings/{lint['id']}", json={"ticked": True})
    assert response.status_code == 400 and response.get_json()["code"] == "report_only"
    assert "report only" in response.get_json()["error"]


def test_ticking_needs_a_boolean_and_a_real_finding(client):
    scan = post_scan(client).get_json()["scan"]
    finding_id = scan["findings"][0]["id"]
    assert client.patch(f"/api/findings/{finding_id}", json={"ticked": "yes"}).status_code == 400
    assert client.patch("/api/findings/99999", json={"ticked": True}).status_code == 404


def test_the_database_refuses_a_ticked_report_only_row(app):
    post = app.test_client().post("/api/scans", json=REPO).get_json()["scan"]
    with app.extensions["lopper_pool"].connection() as conn:
        with pytest.raises(psycopg.errors.CheckViolation):
            conn.execute("UPDATE findings SET ticked = TRUE WHERE scan_id = %s AND report_only", (post["id"],))


def test_a_repo_that_cannot_be_cloned_fails_with_a_clear_message(make_app):
    @contextmanager
    def private_repo(ref):
        raise RepoError(f"We couldn't clone {ref.url}. Lopper can only read public repos right now. Your code hasn't been changed.")
        yield  # pragma: no cover

    client = make_app(fetch=private_repo).test_client()
    scan = post_scan(client).get_json()["scan"]
    assert scan["status"] == "failed"
    assert "public repos" in scan["error"] and "hasn't been changed" in scan["error"]
    assert scan["findings"] == []
    # A failed scan can simply be retried.
    assert post_scan(client).status_code == 202


def test_an_unexpected_crash_is_reported_without_leaking_details(make_app):
    @contextmanager
    def crashing(ref):
        raise RuntimeError("secret internal path /srv/x")
        yield  # pragma: no cover

    scan = post_scan(make_app(fetch=crashing).test_client()).get_json()["scan"]
    assert scan["status"] == "failed"
    assert "secret" not in scan["error"] and "hasn't been changed" in scan["error"]


def test_a_scan_already_running_is_returned_instead_of_starting_another(client, app):
    with app.extensions["lopper_pool"].connection() as conn:
        repo = conn.execute(
            "INSERT INTO repos (url, owner, name) VALUES ('https://github.com/acme/web-platform', 'acme', 'web-platform') RETURNING id"
        ).fetchone()
        running = conn.execute("INSERT INTO scans (repo_id, status) VALUES (%s, 'running') RETURNING id", (repo["id"],)).fetchone()
    response = post_scan(client)
    assert response.status_code == 200
    assert response.get_json()["scan"]["id"] == running["id"] and response.get_json()["scan"]["status"] == "running"


def test_a_stuck_scan_is_replaced_after_the_stale_limit(client, app):
    with app.extensions["lopper_pool"].connection() as conn:
        repo = conn.execute(
            "INSERT INTO repos (url, owner, name) VALUES ('https://github.com/acme/web-platform', 'acme', 'web-platform') RETURNING id"
        ).fetchone()
        stuck = conn.execute(
            "INSERT INTO scans (repo_id, status, started_at) VALUES (%s, 'running', now() - interval '1 hour') RETURNING id",
            (repo["id"],),
        ).fetchone()
    response = post_scan(client)
    assert response.status_code == 202
    assert response.get_json()["scan"]["id"] != stuck["id"] and response.get_json()["scan"]["status"] == "done"


def test_starting_scans_is_rate_limited(make_app):
    client = make_app(scans_per_minute=2).test_client()
    assert post_scan(client).status_code == 202
    assert post_scan(client).status_code == 202
    limited = post_scan(client)
    assert limited.status_code == 429 and limited.get_json()["code"] == "rate_limited"
    assert "Nothing has been changed" in limited.get_json()["error"]


def test_scans_can_run_in_the_background(make_app):
    client = make_app(scan_inline=False).test_client()
    response = post_scan(client)
    assert response.status_code == 202
    scan_id = response.get_json()["scan"]["id"]
    scan = None
    for _ in range(50):
        scan = client.get(f"/api/scans/{scan_id}").get_json()["scan"]
        if scan["status"] != "running":
            break
        time.sleep(0.1)
    assert scan["status"] == "done" and scan["counts"]["unused-package"] == 1


def test_cors_allows_the_front_end_origin_only(client):
    allowed = client.get("/api/health", headers={"Origin": "http://localhost:5173"})
    assert allowed.headers.get("Access-Control-Allow-Origin") == "http://localhost:5173"
    other = client.get("/api/health", headers={"Origin": "https://evil.example"})
    assert "Access-Control-Allow-Origin" not in other.headers


def test_oversized_bodies_are_refused(client):
    response = client.post("/api/scans", data="x" * 20_000, content_type="application/json")
    assert response.status_code == 413
