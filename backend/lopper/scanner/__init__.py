"""The scanner reads a folder and returns findings with evidence. It never changes the code it reads."""

from __future__ import annotations

from pathlib import Path

from . import golang, js, python
from .models import Finding, ScanResult
from .walk import MAX_FILES, ScanLimitError, collect_files

__all__ = ["Finding", "ScanLimitError", "ScanResult", "scan_path"]

_ORDER = {"unused-package": 0, "unused-dev-dependency": 1, "unused-export": 2, "lint-issue": 3}


def scan_path(root: str | Path, include_lint: bool = True, max_files: int = MAX_FILES) -> ScanResult:
    """Scan a folder for unused packages, dev dependencies and exports, plus lint issues (report only)."""
    root = Path(root)
    if not root.is_dir():
        raise NotADirectoryError(f"{root} is not a folder.")
    files = collect_files(root, max_files=max_files)

    js_result = js.analyze(files, include_lint=include_lint)
    py_result = python.analyze(files, include_lint=include_lint)
    go_result = golang.analyze(files)

    languages = []
    if js_result.files_scanned or js_result.packages_scanned:
        languages.append("javascript")
    if py_result.files_scanned:
        languages.append("python")
    if go_result.packages_scanned:
        languages.append("go")

    findings = js_result.findings + py_result.findings + go_result.findings
    findings.sort(key=lambda f: (_ORDER[f.type], f.package, f.file_path, f.line or 0, f.item))
    return ScanResult(
        findings=findings,
        files_scanned=js_result.files_scanned + py_result.files_scanned + go_result.files_scanned,
        packages_scanned=js_result.packages_scanned + py_result.packages_scanned + go_result.packages_scanned,
        languages=languages,
    )
