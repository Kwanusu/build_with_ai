"""Reads a `.env` file into the environment, so secrets can live in a git-ignored file instead of a shell history."""

from __future__ import annotations

import os
from pathlib import Path


def load_dotenv(path: str | Path | None = None) -> list[str]:
    """Set variables from a .env file unless they are already set. Returns the names it set.

    With no `path` it reads `.env` in the current folder, then in `backend/`, then in the project root,
    so the file can live wherever is handiest. Earlier files win over later ones.
    """
    if path is None:
        here = Path(__file__).resolve().parent.parent  # backend/
        loaded: list[str] = []
        for candidate in (Path(".env"), here / ".env", here.parent / ".env"):
            if candidate.is_file():
                loaded += [name for name in load_dotenv(candidate) if name not in loaded]
        return loaded
    file = Path(path)
    if not file.is_file():
        return []
    loaded = []
    for raw in file.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, _, value = line.partition("=")
        name = name.strip().removeprefix("export ").strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        elif " #" in value:
            value = value.split(" #", 1)[0].rstrip()
        if name and name not in os.environ:  # a variable you set yourself wins
            os.environ[name] = value
            loaded.append(name)
    return loaded
