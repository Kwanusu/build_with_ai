from __future__ import annotations

import os
from dataclasses import dataclass, field, replace
from urllib.parse import urlsplit

DEFAULT_DATABASE_URL = "postgresql://lopper@localhost:5544/lopper"
DEFAULT_FRONTEND_URL = "http://localhost:5173"


@dataclass(frozen=True)
class Config:
    database_url: str = DEFAULT_DATABASE_URL
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
    secret_key: str | None = None
    # Scopes asked for at sign-in. `repo` lets Lopper read private repos you can access (and, later, open pull requests).
    github_scopes: str = "read:user repo"
    # Where the browser is sent after sign-in, and the site that is allowed to call the API with cookies.
    frontend_url: str = DEFAULT_FRONTEND_URL
    session_days: int = 30
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
        config = cls(
            database_url=env.get("DATABASE_URL", DEFAULT_DATABASE_URL),
            cors_origins=tuple(
                origin.strip() for origin in env.get("CORS_ORIGINS", ",".join(cls.cors_origins)).split(",") if origin.strip()
            ),
            scan_workers=int(env.get("SCAN_WORKERS", cls.scan_workers)),
            scans_per_minute=int(env.get("SCANS_PER_MINUTE", cls.scans_per_minute)),
            github_client_id=env.get("GITHUB_CLIENT_ID") or None,
            github_client_secret=env.get("GITHUB_CLIENT_SECRET") or None,
            secret_key=env.get("SECRET_KEY") or None,
            github_scopes=env.get("GITHUB_SCOPES", cls.github_scopes),
            frontend_url=env.get("FRONTEND_URL", DEFAULT_FRONTEND_URL).rstrip("/"),
        )
        return replace(config, **overrides) if overrides else config
