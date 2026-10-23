"""Signing in with GitHub, and the list of the signed-in person's repos."""

from __future__ import annotations

from flask import Blueprint, current_app, jsonify, make_response, redirect, request

from .auth import (
    SESSION_COOKIE, STATE_COOKIE, STATE_MAX_AGE_SECONDS, create_session, end_all_sessions, end_session, new_state, state_matches,
)
from .github import GitHubError
from .routes import current_user, error, github_token

bp = Blueprint("auth", __name__, url_prefix="/api")


def _config():
    return current_app.extensions["lopper_config"]


def _github():
    return current_app.extensions["lopper_github"]


def _cookie_options() -> dict:
    return {"httponly": True, "samesite": "Lax", "secure": _config().cookie_secure, "path": "/"}


def _back_to_site(reason: str | None = None):
    """Send the browser back to the site: the Connect screen, or the sign-in error page."""
    target = f"{_config().frontend_url}/#/scan" if reason is None else f"{_config().frontend_url}/#/auth/error/{reason}"
    response = redirect(target, code=302)
    response.delete_cookie(STATE_COOKIE, path="/")
    return response


@bp.get("/auth/me")
def me():
    user = current_user()
    return jsonify(
        {
            "user": {"login": user["login"], "avatar_url": user["avatar_url"]} if user else None,
            "sign_in_available": _config().auth_enabled,
        }
    )


@bp.get("/auth/github/login")
def login():
    config = _config()
    if not config.auth_enabled:
        return _back_to_site("not_configured")
    state, signed = new_state(config.secret_key)
    response = redirect(_github().authorize_url(state), code=302)
    response.set_cookie(STATE_COOKIE, signed, max_age=STATE_MAX_AGE_SECONDS, **_cookie_options())
    return response


@bp.get("/auth/github/callback")
def callback():
    config = _config()
    if not config.auth_enabled:
        return _back_to_site("not_configured")
    if request.args.get("error"):
        return _back_to_site("access_denied")
    if not state_matches(config.secret_key, request.cookies.get(STATE_COOKIE), request.args.get("state")):
        return _back_to_site("invalid_state")
    code = request.args.get("code")
    if not code:
        return _back_to_site("access_denied")

    try:
        token = _github().exchange_code(code)
        profile = _github().get_user(token)
    except GitHubError as problem:
        return _back_to_site("github_unavailable" if problem.code == "unavailable" else "invalid_code")

    pool = current_app.extensions["lopper_pool"]
    encrypted = current_app.extensions["lopper_tokens"].encrypt(token)
    with pool.connection() as conn:
        user = conn.execute(
            """INSERT INTO users (github_id, login, avatar_url, access_token_encrypted)
               VALUES (?, ?, ?, ?)
               ON CONFLICT (github_id) DO UPDATE SET login = EXCLUDED.login, avatar_url = EXCLUDED.avatar_url,
                   access_token_encrypted = EXCLUDED.access_token_encrypted, last_signed_in_at = now()
               RETURNING id""",
            (profile["id"], profile["login"], profile["avatar_url"], encrypted),
        ).fetchone()
    session_token = create_session(pool, user["id"], config.session_days)

    response = _back_to_site()
    response.set_cookie(SESSION_COOKIE, session_token, max_age=config.session_days * 86400, **_cookie_options())
    return response


@bp.post("/auth/logout")
def logout():
    end_session(current_app.extensions["lopper_pool"], request.cookies.get(SESSION_COOKIE))
    response = make_response(jsonify({"ok": True}))
    response.delete_cookie(SESSION_COOKIE, path="/")
    return response


@bp.get("/repos")
def list_repos():
    user = current_user()
    if not user:
        return error("Sign in with GitHub to see your repos.", "sign_in_required", 401)
    token = github_token(user)
    if token is None:
        return error("We couldn't read your GitHub sign-in, so please sign in again.", "sign_in_required", 401)
    try:
        repos = _github().list_repos(token)
    except GitHubError as problem:
        if problem.code == "token_invalid":
            end_all_sessions(current_app.extensions["lopper_pool"], user["id"])
            response = make_response(
                jsonify({"error": "GitHub no longer accepts your sign-in. Sign in again to see your repos.", "code": "sign_in_required"}), 401
            )
            response.delete_cookie(SESSION_COOKIE, path="/")
            return response
        return error("We couldn't reach GitHub to list your repos. Try again in a moment. Nothing has been changed.", "github_unavailable", 502)
    return jsonify({"repos": repos})
