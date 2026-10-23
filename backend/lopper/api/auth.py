"""Sessions, signed sign-in state, and encrypting GitHub tokens at rest."""

from __future__ import annotations

import base64
import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from cryptography.fernet import Fernet, InvalidToken
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from .db import Database

SESSION_COOKIE = "lopper_session"
STATE_COOKIE = "lopper_oauth_state"
STATE_MAX_AGE_SECONDS = 600


class TokenBox:
    """Encrypts GitHub access tokens so a copy of the database can't be used to act as someone."""

    def __init__(self, secret_key: str) -> None:
        key = base64.urlsafe_b64encode(hashlib.sha256(f"lopper-token-box:{secret_key}".encode()).digest())
        self._fernet = Fernet(key)

    def encrypt(self, token: str) -> str:
        return self._fernet.encrypt(token.encode()).decode()

    def decrypt(self, encrypted: str) -> str | None:
        try:
            return self._fernet.decrypt(encrypted.encode()).decode()
        except InvalidToken:
            return None


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def new_state(secret_key: str) -> tuple[str, str]:
    """A random sign-in state and the signed copy that goes in a cookie. Returns (state, cookie_value)."""
    state = secrets.token_urlsafe(24)
    return state, URLSafeTimedSerializer(secret_key, salt="lopper-oauth-state").dumps(state)


def state_matches(secret_key: str, cookie_value: str | None, state: str | None) -> bool:
    if not cookie_value or not state:
        return False
    try:
        expected = URLSafeTimedSerializer(secret_key, salt="lopper-oauth-state").loads(cookie_value, max_age=STATE_MAX_AGE_SECONDS)
    except (BadSignature, SignatureExpired):
        return False
    return secrets.compare_digest(expected, state)


def create_session(pool: Database, user_id: int, days: int) -> str:
    token = secrets.token_urlsafe(32)
    expires = datetime.now(timezone.utc) + timedelta(days=days)
    with pool.connection() as conn:
        conn.execute("DELETE FROM sessions WHERE expires_at < now()")
        conn.execute(
            "INSERT INTO sessions (token_hash, user_id, expires_at) VALUES (?, ?, ?)", (hash_token(token), user_id, expires)
        )
    return token


def user_for_session(pool: Database, token: str | None) -> dict | None:
    if not token:
        return None
    with pool.connection() as conn:
        return conn.execute(
            """SELECT u.id, u.github_id, u.login, u.avatar_url, u.access_token_encrypted
               FROM sessions s JOIN users u ON u.id = s.user_id
               WHERE s.token_hash = ? AND s.expires_at > now()""",
            (hash_token(token),),
        ).fetchone()


def end_session(pool: Database, token: str | None) -> None:
    if token:
        with pool.connection() as conn:
            conn.execute("DELETE FROM sessions WHERE token_hash = ?", (hash_token(token),))


def end_all_sessions(pool: Database, user_id: int) -> None:
    with pool.connection() as conn:
        conn.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
