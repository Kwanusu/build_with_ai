from __future__ import annotations

import os
from dataclasses import dataclass, field, replace

DEFAULT_DATABASE_URL = "postgresql://lopper@localhost:5544/lopper"


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
    extra: dict = field(default_factory=dict)

    @classmethod
    def from_env(cls, **overrides) -> "Config":
        config = cls(
            database_url=os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL),
            cors_origins=tuple(
                origin.strip() for origin in os.environ.get("CORS_ORIGINS", ",".join(cls.cors_origins)).split(",") if origin.strip()
            ),
            scan_workers=int(os.environ.get("SCAN_WORKERS", cls.scan_workers)),
            scans_per_minute=int(os.environ.get("SCANS_PER_MINUTE", cls.scans_per_minute)),
        )
        return replace(config, **overrides) if overrides else config
