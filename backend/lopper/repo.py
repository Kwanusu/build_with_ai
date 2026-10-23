"""Fetching a repo from a pasted URL.

Only github.com repositories are accepted, so a pasted URL can't point the server at an internal
address. We clone read-only into a temp folder, never run anything from it, and delete it.
"""

from __future__ import annotations

import base64
import os
import re
import shutil
import stat
import subprocess
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

GITHUB_URL_RE = re.compile(
    r"^(?:https://)?(?:www\.)?github\.com/([A-Za-z0-9](?:[A-Za-z0-9-]{0,38}))/([A-Za-z0-9_.-]{1,100}?)(?:\.git)?/?$"
)
CLONE_TIMEOUT_SECONDS = 90
MAX_CHECKOUT_BYTES = 400 * 1024 * 1024


class RepoError(Exception):
    """A repo we can't use. The message is written to be shown to the person who pasted the URL."""


@dataclass(frozen=True)
class RepoRef:
    owner: str
    name: str

    @property
    def url(self) -> str:
        return f"https://github.com/{self.owner}/{self.name}"


def parse_repo_url(raw: str) -> RepoRef:
    """Turn what someone pasted into a RepoRef, or explain what's wrong."""
    cleaned = (raw or "").strip()
    match = GITHUB_URL_RE.match(cleaned)
    if not match or match.group(2) in {".", ".."}:
        raise RepoError("That doesn't look like a GitHub repo URL. Paste one like https://github.com/owner/repo.")
    return RepoRef(owner=match.group(1), name=match.group(2))


def _make_writable_and_retry(function, path, _excinfo) -> None:
    os.chmod(path, stat.S_IWRITE)
    function(path)


def _remove_tree(path: Path) -> None:
    # Git marks pack files read-only, which stops a plain delete on Windows.
    shutil.rmtree(path, onexc=lambda fn, p, exc: _make_writable_and_retry(fn, p, exc))


def _folder_size(path: Path) -> int:
    total = 0
    for current, _dirs, names in os.walk(path):
        for name in names:
            try:
                total += os.lstat(os.path.join(current, name)).st_size
            except OSError:
                pass
    return total


@contextmanager
def checkout(ref: RepoRef, timeout: int = CLONE_TIMEOUT_SECONDS, token: str | None = None) -> Iterator[Path]:
    """Shallow-clone a repo into a temp folder and delete it afterwards.

    Without a token only public repos work. With a signed-in person's GitHub token, repos they can
    access work too. The token goes to git through the environment, never the command line, so it
    can't show up in a process list, and no message here ever includes it.
    """
    workdir = Path(tempfile.mkdtemp(prefix="lopper-"))
    target = workdir / "repo"
    env = {
        **os.environ,
        "GIT_TERMINAL_PROMPT": "0",  # never ask for a password: private repos should fail, not hang
        "GIT_ASKPASS": "",
        "GIT_CONFIG_NOSYSTEM": "1",
    }
    if token:
        credentials = base64.b64encode(f"x-access-token:{token}".encode()).decode()
        env.update(
            GIT_CONFIG_COUNT="1",
            GIT_CONFIG_KEY_0="http.https://github.com/.extraheader",
            GIT_CONFIG_VALUE_0=f"AUTHORIZATION: basic {credentials}",
        )
    command = [
        "git", "-c", "core.symlinks=false", "-c", "core.hooksPath=", "-c", "protocol.allow=never",
        "-c", "protocol.https.allow=always", "clone", "--depth", "1", "--single-branch", "--no-tags",
        "--filter=blob:limit=1048576", "--", ref.url + ".git", str(target),
    ]
    try:
        try:
            completed = subprocess.run(command, env=env, capture_output=True, text=True, timeout=timeout, check=False)
        except subprocess.TimeoutExpired as error:
            raise RepoError(
                "Cloning took too long, so we stopped. Your code hasn't been changed. Try again, or scan a smaller repo."
            ) from error
        except FileNotFoundError as error:
            raise RepoError("Git isn't installed on the machine running Lopper, so we can't fetch the repo.") from error
        if completed.returncode != 0:
            if token:
                raise RepoError(
                    f"We couldn't clone {ref.url}. Check the URL, and that the GitHub account you signed in with can read it. "
                    "Your code hasn't been changed."
                )
            raise RepoError(
                f"We couldn't clone {ref.url}. Without signing in, Lopper can only read public repos. "
                "Check the URL, or sign in with GitHub to scan a private repo. Your code hasn't been changed."
            )
        if _folder_size(target) > MAX_CHECKOUT_BYTES:
            raise RepoError("This repo is larger than we scan at once. Your code hasn't been changed.")
        yield target
    finally:
        _remove_tree(workdir)
