from __future__ import annotations

import threading
import time
from collections import defaultdict, deque

from flask import Blueprint, current_app, jsonify, request

from ..repo import RepoError, parse_repo_url
from ..scanner.models import FINDING_TYPES
from .db import database_is_up

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
    if not limiter.allow(request.remote_addr or "unknown"):
        return error("That's a lot of scans in a minute. Wait a moment and try again. Nothing has been changed.", "rate_limited", 429)

    scan, created = service().start(ref)
    return jsonify({"scan": scan}), 202 if created else 200


@bp.get("/scans/<int:scan_id>")
def get_scan(scan_id: int):
    finding_type = request.args.get("type")
    if finding_type and finding_type not in FINDING_TYPES:
        return error(f"Unknown finding type. Use one of: {', '.join(FINDING_TYPES)}.", "invalid_type", 400)
    scan = service().get_scan(scan_id, finding_type)
    if not scan:
        return error("We couldn't find that scan. It may have been replaced by a newer scan of the same repo.", "not_found", 404)
    return jsonify({"scan": scan})


@bp.get("/repos/<owner>/<name>/scan")
def latest_scan(owner: str, name: str):
    try:
        ref = parse_repo_url(f"https://github.com/{owner}/{name}")
    except RepoError as problem:
        return error(str(problem), "invalid_repo_url", 400)
    scan = service().latest_for_repo(ref)
    if not scan:
        return error("We haven't scanned that repo yet.", "not_found", 404)
    return jsonify({"scan": scan})


@bp.patch("/findings/<int:finding_id>")
def update_finding(finding_id: int):
    body = request.get_json(silent=True)
    if not isinstance(body, dict) or not isinstance(body.get("ticked"), bool):
        return error("Send a JSON body like {\"ticked\": true}.", "invalid_request", 400)
    finding, problem = service().set_ticked(finding_id, body["ticked"])
    if problem == "not_found":
        return error("We couldn't find that finding.", "not_found", 404)
    if problem == "report_only":
        return error("Lint issues are report only, so there's nothing to tick.", "report_only", 400)
    return jsonify({"finding": finding})
