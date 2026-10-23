"""Starting scans, running them in the background, and reading them back.

Who can see what: a scan made while signed in belongs to that user and only they can read or tick it.
A scan made without signing in is public: anyone can read it, and nobody can tick it.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from contextlib import AbstractContextManager
from datetime import datetime, timedelta, timezone
from pathlib import Path

from ..repo import RepoError, RepoRef, checkout
from ..scanner import ScanLimitError, ScanResult, scan_path
from ..scanner.models import FINDING_TYPES
from .db import Database, format_time, to_iso

log = logging.getLogger(__name__)

# How a repo becomes a folder. `token` is the signed-in person's GitHub token, or None.
Fetcher = Callable[[RepoRef, str | None], AbstractContextManager[Path]]

FINDING_COLUMNS = "id, type, package, item, file_path, line, evidence, confidence, language, report_only, ticked"


def _finding(row: dict | None) -> dict | None:
    """SQLite keeps booleans as 0 and 1; the API says true and false (Postgres already does)."""
    if row is None:
        return None
    return {**row, "report_only": bool(row["report_only"]), "ticked": bool(row["ticked"])}


def default_fetch(ref: RepoRef, token: str | None) -> AbstractContextManager[Path]:
    return checkout(ref, token=token)


class ScanService:
    def __init__(
        self,
        pool: Database,
        fetch: Fetcher = default_fetch,
        workers: int = 2,
        inline: bool = False,
        stale_minutes: int = 10,
    ) -> None:
        self.pool = pool
        self.fetch = fetch
        self.inline = inline
        self.stale_minutes = stale_minutes
        self.executor = None if inline else ThreadPoolExecutor(max_workers=workers, thread_name_prefix="lopper-scan")

    # ----- starting -----

    def start(self, ref: RepoRef, user_id: int | None = None, token: str | None = None) -> tuple[dict, bool]:
        """Begin a scan of `ref` for `user_id` (None for a public scan).

        Returns (scan, created). If that user's scan of the repo is already running, returns it instead.
        """
        stale_before = format_time(datetime.now(timezone.utc) - timedelta(minutes=self.stale_minutes))
        with self.pool.connection(write=True) as conn:
            repo = conn.execute(
                """INSERT INTO repos (url, owner, name) VALUES (?, ?, ?)
                   ON CONFLICT (url) DO UPDATE SET url = EXCLUDED.url RETURNING id""",
                (ref.url, ref.owner, ref.name),
            ).fetchone()
            # `IS` (not `=`) so that a public scan, whose user_id is NULL, matches too.
            running = conn.execute(
                "SELECT id FROM scans WHERE repo_id = ? AND user_id IS ? AND status = 'running' AND started_at > ?",
                (repo["id"], user_id, stale_before),
            ).fetchone()
            if running:
                scan_id = running["id"]
                created = False
            else:
                # Only the latest scan is kept for each repo and owner, so the old one (and its findings) goes.
                conn.execute("DELETE FROM scans WHERE repo_id = ? AND user_id IS ?", (repo["id"], user_id))
                scan_id = conn.execute(
                    "INSERT INTO scans (repo_id, user_id, status) VALUES (?, ?, 'running') RETURNING id", (repo["id"], user_id)
                ).fetchone()["id"]
                created = True
        if not created:
            return self.get_scan(scan_id, viewer_id=user_id), False
        if self.inline:
            self._run(scan_id, ref, token)
        else:
            self.executor.submit(self._run, scan_id, ref, token)
        return self.get_scan(scan_id, viewer_id=user_id), True

    # ----- running -----

    def _run(self, scan_id: int, ref: RepoRef, token: str | None) -> None:
        try:
            with self.fetch(ref, token) as folder:
                result = scan_path(folder)
        except (RepoError, ScanLimitError) as error:
            self._fail(scan_id, str(error))
        except Exception:  # noqa: BLE001 - a scan must always end in done or failed
            log.exception("Scan %s of %s crashed", scan_id, ref.url)
            self._fail(scan_id, "Something went wrong on our side while scanning. Your code hasn't been changed. Try again in a moment.")
        else:
            self._finish(scan_id, result)

    def _finish(self, scan_id: int, result: ScanResult) -> None:
        with self.pool.connection() as conn:
            updated = conn.execute(
                """UPDATE scans SET status = 'done', finished_at = now(), files_scanned = ?,
                   packages_scanned = ?, languages = ? WHERE id = ? RETURNING id""",
                (result.files_scanned, result.packages_scanned, json.dumps(list(result.languages)), scan_id),
            ).fetchone()
            if not updated:
                return  # a newer scan replaced this one while it ran
            rows = [
                (
                    scan_id, f.type, f.package, f.item, f.file_path, f.line, f.evidence, f.confidence, f.language,
                    f.report_only,
                    # Safe findings start ticked. Uncertain ones and lint issues start unticked.
                    f.confidence == "safe" and not f.report_only,
                )
                for f in result.findings
            ]
            conn.executemany(
                """INSERT INTO findings (scan_id, type, package, item, file_path, line, evidence, confidence,
                   language, report_only, ticked) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                rows,
            )

    def _fail(self, scan_id: int, message: str) -> None:
        with self.pool.connection() as conn:
            conn.execute(
                "UPDATE scans SET status = 'failed', finished_at = now(), error = ? WHERE id = ?", (message, scan_id)
            )

    # ----- reading -----

    def get_scan(self, scan_id: int, finding_type: str | None = None, viewer_id: int | None = None) -> dict | None:
        """The scan, or None if it doesn't exist or belongs to someone else."""
        with self.pool.connection() as conn:
            scan = conn.execute(
                """SELECT s.*, r.url, r.owner, r.name FROM scans s JOIN repos r ON r.id = s.repo_id WHERE s.id = ?""",
                (scan_id,),
            ).fetchone()
            if not scan or (scan["user_id"] is not None and scan["user_id"] != viewer_id):
                return None
            counts = {kind: 0 for kind in FINDING_TYPES}
            for row in conn.execute("SELECT type, count(*) AS n FROM findings WHERE scan_id = ? GROUP BY type", (scan_id,)):
                counts[row["type"]] = row["n"]
            query = f"SELECT {FINDING_COLUMNS} FROM findings WHERE scan_id = ?"
            params: list = [scan_id]
            if finding_type:
                query += " AND type = ?"
                params.append(finding_type)
            findings = [_finding(row) for row in conn.execute(query + " ORDER BY type, package, file_path, line, id", params)]
        return {
            "id": scan["id"],
            "status": scan["status"],
            "repo": {"url": scan["url"], "owner": scan["owner"], "name": scan["name"]},
            "started_at": to_iso(scan["started_at"]),
            "finished_at": to_iso(scan["finished_at"]),
            "error": scan["error"],
            "files_scanned": scan["files_scanned"],
            "packages_scanned": scan["packages_scanned"],
            "languages": json.loads(scan["languages"]),
            "counts": counts,
            # Only the person who made a scan while signed in can tick items on it.
            "can_tick": scan["user_id"] is not None and scan["user_id"] == viewer_id,
            "findings": findings,
        }

    def latest_for_repo(self, ref: RepoRef, viewer_id: int | None = None) -> dict | None:
        """The viewer's own scan of the repo if they have one, otherwise the public one."""
        with self.pool.connection() as conn:
            row = conn.execute(
                """SELECT s.id FROM scans s JOIN repos r ON r.id = s.repo_id
                   WHERE r.url = ? AND (s.user_id IS NULL OR s.user_id = ?)
                   ORDER BY (s.user_id IS NULL), s.started_at DESC LIMIT 1""",
                (ref.url, viewer_id),
            ).fetchone()
        return self.get_scan(row["id"], viewer_id=viewer_id) if row else None

    def set_ticked(self, finding_id: int, ticked: bool, user_id: int) -> tuple[dict | None, str | None]:
        """Tick or untick a finding. Returns (finding, problem).

        `problem` is "not_found" (no such finding, or it is in someone else's private scan),
        "public_scan" (a public scan can't be ticked), or "report_only".
        """
        with self.pool.connection() as conn:
            current = conn.execute(
                "SELECT f.report_only, s.user_id FROM findings f JOIN scans s ON s.id = f.scan_id WHERE f.id = ?", (finding_id,)
            ).fetchone()
            if not current or (current["user_id"] is not None and current["user_id"] != user_id):
                return None, "not_found"
            if current["user_id"] is None:
                return None, "public_scan"
            if current["report_only"]:
                return None, "report_only"
            finding = conn.execute(
                f"UPDATE findings SET ticked = ? WHERE id = ? RETURNING {FINDING_COLUMNS}", (ticked, finding_id)
            ).fetchone()
        return _finding(finding), None
