from __future__ import annotations

import atexit
from urllib.parse import urlsplit

from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.exceptions import HTTPException

from . import auth_routes
from .auth import TokenBox
from .config import Config
from .db import init_db, make_pool
from .github import GitHubClient
from .routes import RateLimiter, bp
from .scans import Fetcher, ScanService, default_fetch

__all__ = ["Config", "create_app"]

UNSAFE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})


def create_app(
    config: Config | None = None, fetch: Fetcher = default_fetch, init: bool = True, github: GitHubClient | None = None
) -> Flask:
    """Build the Flask app. `fetch` is how a repo URL becomes a folder and `github` talks to GitHub; tests swap both."""
    config = config or Config.from_env()
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024
    app.config["JSON_SORT_KEYS"] = False

    pool = make_pool(config.database_url)
    atexit.register(pool.close)
    app.extensions["lopper_config"] = config
    app.extensions["lopper_pool"] = pool
    app.extensions["lopper_limiter"] = RateLimiter(config.scans_per_minute)
    app.extensions["lopper_scans"] = ScanService(
        pool, fetch=fetch, workers=config.scan_workers, inline=config.scan_inline, stale_minutes=config.stale_scan_minutes
    )
    # Sign-in is only switched on when the GitHub app and a secret key are configured.
    app.extensions["lopper_tokens"] = TokenBox(config.secret_key or "sign-in-is-off")
    app.extensions["lopper_github"] = github or (
        GitHubClient(config.github_client_id, config.github_client_secret, config.github_scopes) if config.auth_enabled else None
    )

    CORS(app, resources={r"/api/*": {"origins": sorted(config.allowed_origins)}}, supports_credentials=True)

    @app.before_request
    def refuse_requests_from_other_sites():
        """Cookies identify people, so a browser request that changes something must come from our own site."""
        if request.method in UNSAFE_METHODS:
            origin = request.headers.get("Origin")
            if origin and origin not in config.allowed_origins:
                return jsonify({"error": "That request came from a site we don't recognise.", "code": "bad_origin"}), 403
        return None

    app.register_blueprint(bp)
    app.register_blueprint(auth_routes.bp)

    @app.errorhandler(HTTPException)
    def http_error(problem: HTTPException):
        messages = {
            404: "We couldn't find that.",
            405: "That method isn't allowed here.",
            413: "That request is too large.",
        }
        return jsonify({"error": messages.get(problem.code, problem.description), "code": "http_error"}), problem.code

    if init:
        with app.app_context():
            init_db()
    return app
