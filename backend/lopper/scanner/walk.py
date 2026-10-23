from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

SKIP_DIRS = frozenset(
    {
        ".git", ".hg", ".svn", "node_modules", "bower_components", "vendor", "dist", "build",
        "out", ".next", ".nuxt", ".turbo", ".cache", ".parcel-cache", "coverage", "target",
        "venv", ".venv", "env", "__pycache__", ".mypy_cache", ".pytest_cache", ".tox",
        ".idea", ".vscode", ".pgdata",
    }
)

MAX_FILES = 20_000
MAX_FILE_BYTES = 1_000_000


class ScanLimitError(Exception):
    """The repo is bigger than we will scan."""


@dataclass
class RepoFiles:
    """Every file under the scan root, as paths relative to it (posix style)."""

    root: Path
    paths: list[str] = field(default_factory=list)

    def read(self, relative: str) -> str | None:
        path = self.root / relative
        try:
            if path.stat().st_size > MAX_FILE_BYTES:
                return None
            return path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return None

    def with_suffix(self, *suffixes: str) -> list[str]:
        return [p for p in self.paths if p.endswith(suffixes)]

    def named(self, *names: str) -> list[str]:
        return [p for p in self.paths if p.rsplit("/", 1)[-1] in names]


def collect_files(root: Path, max_files: int = MAX_FILES) -> RepoFiles:
    """Walk `root`, skipping vendored and generated folders and never following symlinks."""
    root = root.resolve()
    files = RepoFiles(root=root)
    for current, dirs, names in os.walk(root, followlinks=False):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS and not os.path.islink(os.path.join(current, d)))
        for name in sorted(names):
            full = os.path.join(current, name)
            if os.path.islink(full):
                continue
            files.paths.append(Path(full).relative_to(root).as_posix())
            if len(files.paths) > max_files:
                raise ScanLimitError(
                    f"This repo has more than {max_files:,} files, which is more than we scan at once."
                )
    return files


def dirname(path: str) -> str:
    """Directory of a relative path; '.' for the root."""
    head, _, _ = path.rpartition("/")
    return head or "."


def is_under(path: str, directory: str) -> bool:
    return directory == "." or path == directory or path.startswith(directory + "/")


def is_test_path(path: str) -> bool:
    lowered = path.lower()
    name = lowered.rsplit("/", 1)[-1]
    parts = lowered.split("/")
    return (
        any(part in {"test", "tests", "__tests__", "spec", "specs", "e2e", "cypress", "__mocks__"} for part in parts)
        or ".test." in name
        or ".spec." in name
        or name.startswith("test_")
        or name.endswith("_test.py")
        or name.endswith("_test.go")
        or name == "conftest.py"
    )
