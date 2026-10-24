from __future__ import annotations

import hmac
import threading
import time
from collections import defaultdict, deque

from flask import Blueprint, current_app, g, jsonify, make_response, request

from ..chat import ChatRequestError, parse_messages
from ..repo import RepoError, parse_repo_url
from ..scanner.models import FINDING_TYPES
from .assistant import ChatError
from .auth import SESSION_COOKIE, end_all_sessions, user_for_session
from .db import database_is_up
from .github import GitHubError
from .pulls import PullRequestError, github_problem, open_pull_request

bp = Blueprint("api", __name__, url_prefix="/api")


class RateLimiter:
    """A small in-memory limit on how often one address can start scans. One process only."""

    def __init__(self, per_minute: int) -> None:
        self.per_minute = per_minute
        self.hits: dict[str, deque[float]] = defaultdict(deque)
        self.lock = threading.Lock()

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        with self.lock:
            window = self.hits[key]
            while window and now - window[0] > 60:
                window.popleft()
            if len(window) >= self.per_minute:
                return False
            window.append(now)
            return True


def error(message: str, code: str, status: int):
    return jsonify({"error": message, "code": code}), status


def service():
    return current_app.extensions["lopper_scans"]


def client_address() -> str:
    """Who is calling, for the rate limit.

    When the site forwards /api to us (Cloudflare Pages), every request arrives from the forwarder. It sends the real
    address in X-Lopper-Client-IP together with the shared PROXY_SECRET. We believe that header only if the secret
    matches, so nobody else can pick their own address.
    """
    secret = current_app.extensions["lopper_config"].proxy_secret
    sent = request.headers.get("X-Lopper-Proxy-Secret", "")
    forwarded = request.headers.get("X-Lopper-Client-IP", "").strip()
    if secret and forwarded and hmac.compare_digest(sent.encode(), secret.encode()):
        return forwarded[:64]
    return request.remote_addr or "unknown"


def current_user() -> dict | None:
    """The signed-in user for this request, from the session cookie, or None."""
    if "lopper_user" not in g:
        g.lopper_user = user_for_session(current_app.extensions["lopper_pool"], request.cookies.get(SESSION_COOKIE))
    return g.lopper_user


def github_token(user: dict) -> str | None:
    return current_app.extensions["lopper_tokens"].decrypt(user["access_token_encrypted"])


@bp.get("/health")
def health():
    up = database_is_up()
    return jsonify({"status": "ok" if up else "degraded", "database": up}), 200 if up else 503


@bp.post("/scans")
def create_scan():
    body = request.get_json(silent=True)
    if not isinstance(body, dict) or not isinstance(body.get("repo_url"), str):
        return error("Send a JSON body with a repo_url, like {\"repo_url\": \"https://github.com/owner/repo\"}.", "invalid_request", 400)
    try:
        ref = parse_repo_url(body["repo_url"])
    except RepoError as problem:
        return error(str(problem), "invalid_repo_url", 400)

    limiter: RateLimiter = current_app.extensions["lopper_limiter"]
    if not limiter.allow(client_address()):
        return error("That's a lot of scans in a minute. Wait a moment and try again. Nothing has been changed.", "rate_limited", 429)

    user = current_user()
    token = None
    if user:
        token = github_token(user)
        if token is None:
            return error("We couldn't read your GitHub sign-in, so please sign in again. Nothing has been changed.", "sign_in_required", 401)
    scan, created = service().start(ref, user["id"] if user else None, token)
    return jsonify({"scan": scan}), 202 if created else 200


@bp.get("/scans/<int:scan_id>")
def get_scan(scan_id: int):
    finding_type = request.args.get("type")
    if finding_type and finding_type not in FINDING_TYPES:
        return error(f"Unknown finding type. Use one of: {', '.join(FINDING_TYPES)}.", "invalid_type", 400)
    user = current_user()
    scan = service().get_scan(scan_id, finding_type, viewer_id=user["id"] if user else None)
    if not scan:
        return error("We couldn't find that scan. It may have been replaced by a newer scan of the same repo.", "not_found", 404)
    return jsonify({"scan": scan})


@bp.get("/repos/<owner>/<name>/scan")
def latest_scan(owner: str, name: str):
    try:
        ref = parse_repo_url(f"https://github.com/{owner}/{name}")
    except RepoError as problem:
        return error(str(problem), "invalid_repo_url", 400)
    user = current_user()
    scan = service().latest_for_repo(ref, viewer_id=user["id"] if user else None)
    if not scan:
        return error("We haven't scanned that repo yet.", "not_found", 404)
    return jsonify({"scan": scan})


@bp.patch("/findings/<int:finding_id>")
def update_finding(finding_id: int):
    body = request.get_json(silent=True)
    if not isinstance(body, dict) or not isinstance(body.get("ticked"), bool):
        return error("Send a JSON body like {\"ticked\": true}.", "invalid_request", 400)
    user = current_user()
    if not user:
        return error("Sign in with GitHub to tick items and keep your choices.", "sign_in_required", 401)
    finding, problem = service().set_ticked(finding_id, body["ticked"], user["id"])
    if problem == "not_found":
        return error("We couldn't find that finding.", "not_found", 404)
    if problem == "public_scan":
        return error("This is a public scan, so it can't be ticked. Rescan while signed in to tick items on your own copy.", "public_scan", 403)
    if problem == "report_only":
        return error("Lint issues are report only, so there's nothing to tick.", "report_only", 400)
    return jsonify({"finding": finding})


# Up to 10 questions of 1,000 characters and 10 replies of 8,000, with room for JSON. More than the global 16 KB limit.
# create_app raises the limit for this route in its first request hook, before anything can read the body.
CHAT_BODY_LIMIT = 128 * 1024


@bp.post("/scans/<int:scan_id>/chat")
def chat_about_scan(scan_id: int):
    """Answer a question about a finished scan. Anyone who can read the scan can ask, so a private scan is only for its owner."""
    assistant =current_app.extensions["lopper_assistant"]
    if assistant is None:
        return error("Chat isn't set up on this server. Nothing has been changed.", "chat_unavailable", 503)
    try:
        history = parse_messages(request.get_json(silent=True))
    except ChatRequestError as problem:
        return error(str(problem), "invalid_request", 400)

    user = current_user()
    scan = service().get_scan(scan_id, viewer_id=user["id"] if user else None)
    if not scan:
        return error("We couldn't find that scan. It may have been replaced by a newer scan of the same repo.", "not_found", 404)
    if scan["status"] != "done":
        return error("That scan hasn't finished yet. Wait for it to finish, then ask again.", "scan_not_done", 409)

    limiter: RateLimiter = current_app.extensions["lopper_chat_limiter"]
    if not limiter.allow(client_address()):
        return error("That's a lot of questions in a minute. Wait a moment and try again. Nothing has been changed.", "rate_limited", 429)
    # Each question holds one of the API's threads while the model answers, so only a few can wait at once.
    slots = current_app.extensions["lopper_chat_slots"]
    if not slots.acquire(blocking=False):
        return error("The assistant is busy right now. Wait a moment and try again. Nothing has been changed.", "chat_busy", 429)
    try:
        reply = assistant.reply(scan, history)
    except ChatError as problem:
        return error(problem.message, problem.code, problem.status)
    finally:
        slots.release()
    return jsonify({"reply": reply})


@bp.post("/scans/<int:scan_id>/pull-request")
def create_pull_request(scan_id: int):
    """Open a pull request that makes the changes ticked on this scan. See pulls.py."""
    user = current_user()
    if not user:
        return error("Sign in with GitHub to open a pull request.", "sign_in_required", 401)
    github = current_app.extensions["lopper_github"]
    if github is None:
        return error("Sign-in isn't set up on this server, so it can't open pull requests.", "sign_in_unavailable", 503)
    token = github_token(user)
    if token is None:
        return error("We couldn't read your GitHub sign-in, so please sign in again. Nothing has been changed.", "sign_in_required", 401)
    scan = service().get_scan(scan_id, viewer_id=user["id"])
    if not scan:
        return error("We couldn't find that scan. It may have been replaced by a newer scan of the same repo.", "not_found", 404)
    try:
        result = open_pull_request(scan, github, token)
    except PullRequestError as problem:
        return jsonify({"error": problem.message, "code": problem.code, **problem.extra}), problem.status
    except GitHubError as problem:
        if problem.code == "token_invalid":
            end_all_sessions(current_app.extensions["lopper_pool"], user["id"])
            response = make_response(
                jsonify({"error": "GitHub no longer accepts your sign-in. Sign in again to open a pull request. Nothing has been changed.", "code": "sign_in_required"}), 401
            )
            response.delete_cookie(SESSION_COOKIE, path="/")
            return response
        message, code, status = github_problem(problem, f"{scan['repo']['owner']}/{scan['repo']['name']}")
        return error(message, code, status)
    return jsonify(result), 201
