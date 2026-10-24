from __future__ import annotations

import os
from dataclasses import dataclass, field, replace
from pathlib import Path
from urllib.parse import urlsplit

from .db import clean_setting

# backend/lopper.db when run from a checkout. It is git-ignored.
DEFAULT_DATABASE_PATH = str(Path(__file__).resolve().parents[2] / "lopper.db")
DEFAULT_FRONTEND_URL = "http://localhost:5173"


def _github_credentials(env) -> tuple[str | None, str | None, str]:
    """The GitHub OAuth app to sign in with.

    Two apps can be configured side by side in one .env file: CLIENT_ID and CLIENT_SECRET are the local development app
    (its callback is http://localhost:5173/...), and GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET are the deployed one.
    A complete CLIENT_ID and CLIENT_SECRET pair wins, so a developer's machine uses the local app. A host that sets only
    the GITHUB_ pair (Render) uses that one. The two are never mixed: an id from one app with the secret of the other
    would fail at GitHub. The last value says which app was chosen: "local", "deployed" or "" for none.
    """
    local = (env.get("CLIENT_ID") or "").strip(), (env.get("CLIENT_SECRET") or "").strip()
    if all(local):
        return local[0], local[1], "local"
    deployed = (env.get("GITHUB_CLIENT_ID") or "").strip() or None, (env.get("GITHUB_CLIENT_SECRET") or "").strip() or None
    return deployed[0], deployed[1], "deployed" if all(deployed) else ""


def _positive_int(env, name: str, default: int) -> int:
    """A whole number of 1 or more from the environment. Empty means the default. The bad value isn't echoed."""
    raw = (env.get(name) or "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError:
        value = 0
    if value < 1:
        raise RuntimeError(f"{name} must be a whole number of 1 or more. Check the value in .env.")
    return value


@dataclass(frozen=True)
class Config:
    # A SQLite file path, or a postgresql:// address (for example Supabase).
    database: str = DEFAULT_DATABASE_PATH
    cors_origins: tuple[str, ...] = ("http://localhost:5173", "http://127.0.0.1:5173")
    scan_workers: int = 2
    scans_per_minute: int = 6
    # Run scans inside the request instead of in the background. Tests use this so results are ready at once.
    scan_inline: bool = False
    # A scan still "running" after this long is treated as dead, so a crashed worker can't block a repo forever.
    stale_scan_minutes: int = 10

    # GitHub sign-in. It is switched on only when all three of these are set.
    github_client_id: str | None = None
    github_client_secret: str | None = None
    # Which OAuth app those came from: "local", "deployed", or "" when sign-in has no app.
    github_app: str = ""
    secret_key: str | None = None
    # Scopes asked for at sign-in. `repo` lets Lopper read private repos you can access (and, later, open pull requests).
    github_scopes: str = "read:user repo"
    # Where the browser is sent after sign-in, and the site that is allowed to call the API with cookies.
    frontend_url: str = DEFAULT_FRONTEND_URL
    session_days: int = 30
    # Set when the site forwards /api to this server (Cloudflare Pages). It lets the forwarder say who the real client is.
    proxy_secret: str | None = None

    # The chat panel on a results page, answered through OpenRouter. It is switched on only when a key is set.
    # AI_MODEL picks the model, as an OpenRouter id like google/gemini-2.5-flash.
    chat_api_key: str | None = None
    chat_model: str = "google/gemini-2.5-flash"
    # How many chat messages one address can send per minute. Each one is a paid model call.
    chats_per_minute: int = 10
    # How many questions can be waiting on the model at once. Each holds one of the API's 8 threads, so this keeps room
    # for scans, sign-in and the health check.
    chat_max_concurrent: int = 4
    extra: dict = field(default_factory=dict)

    @property
    def auth_enabled(self) -> bool:
        return bool(self.github_client_id and self.github_client_secret and self.secret_key)

    @property
    def cookie_secure(self) -> bool:
        return self.frontend_url.startswith("https://")

    @property
    def allowed_origins(self) -> frozenset[str]:
        parts = urlsplit(self.frontend_url)
        return frozenset({*self.cors_origins, f"{parts.scheme}://{parts.netloc}"})

    @classmethod
    def from_env(cls, **overrides) -> "Config":
        env = os.environ
        client_id, client_secret, github_app = _github_credentials(env)
        config = cls(
            database=clean_setting(env.get("DATABASE_URL") or env.get("DATABASE_PATH") or "") or DEFAULT_DATABASE_PATH,
            cors_origins=tuple(
                origin.strip() for origin in env.get("CORS_ORIGINS", ",".join(cls.cors_origins)).split(",") if origin.strip()
            ),
            scan_workers=int(env.get("SCAN_WORKERS", cls.scan_workers)),
            scans_per_minute=int(env.get("SCANS_PER_MINUTE", cls.scans_per_minute)),
            github_client_id=client_id,
            github_client_secret=client_secret,
            github_app=github_app,
            secret_key=env.get("SECRET_KEY") or None,
            github_scopes=env.get("GITHUB_SCOPES", cls.github_scopes),
            # A value pasted into a host's settings often brings a stray space or newline. Without cleaning, a newline in
            # the site address made every redirect after sign-in a 500 and the cookies not Secure (it didn't start with https).
            frontend_url=clean_setting(env.get("FRONTEND_URL") or "").rstrip("/") or DEFAULT_FRONTEND_URL,
            proxy_secret=clean_setting(env.get("PROXY_SECRET") or "") or None,
            chat_api_key=clean_setting(env.get("OPEN_ROUTER_API_KEY") or env.get("OPENROUTER_API_KEY") or "") or None,
            chat_model=clean_setting(env.get("AI_MODEL") or "") or cls.chat_model,
            chats_per_minute=_positive_int(env, "CHATS_PER_MINUTE", cls.chats_per_minute),
        )
        return replace(config, **overrides) if overrides else config
