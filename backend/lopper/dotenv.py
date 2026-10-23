"""Reads a `.env` file into the environment, so secrets can live in a git-ignored file instead of a shell history."""

from __future__ import annotations

import os
from pathlib import Path


def load_dotenv(path: str | Path = ".env") -> list[str]:
    """Set variables from `path` unless they are already set. Returns the names it set."""
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
