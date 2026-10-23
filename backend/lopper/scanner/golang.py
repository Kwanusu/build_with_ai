"""Go: unused direct requirements in go.mod.

We compare the modules a go.mod requires with the packages the .go files import. Unused exports are
not checked for Go yet: finding them reliably needs the compiler's type information.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .models import SAFE, UNUSED_PACKAGE, Finding
from .walk import RepoFiles, dirname, is_under

REQUIRE_LINE_RE = re.compile(r"^\s*([^\s/][^\s]*)\s+(v[^\s]+)(\s*//\s*indirect)?\s*$")
IMPORT_BLOCK_RE = re.compile(r"^\s*import\s*\((.*?)\)", re.S | re.M)
IMPORT_SINGLE_RE = re.compile(r'^\s*import\s+(?:[\w._]+\s+)?"([^"]+)"', re.M)
IMPORT_PATH_RE = re.compile(r'^\s*(?:[\w._]+\s+)?"([^"]+)"', re.M)


@dataclass
class GoAnalysis:
    findings: list[Finding] = field(default_factory=list)
    files_scanned: int = 0
    packages_scanned: int = 0


def _requirements(text: str) -> list[tuple[str, int]]:
    found: list[tuple[str, int]] = []
    in_block = False
    for number, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith("require ("):
            in_block = True
            continue
        if in_block and stripped == ")":
            in_block = False
            continue
        candidate = stripped[len("require "):] if stripped.startswith("require ") else (line if in_block else None)
        if candidate is None:
            continue
        match = REQUIRE_LINE_RE.match(candidate)
        if match and not match.group(3):
            found.append((match.group(1), number))
    return found


def _imports(text: str) -> set[str]:
    paths = set(IMPORT_SINGLE_RE.findall(text))
    for block in IMPORT_BLOCK_RE.findall(text):
        paths.update(IMPORT_PATH_RE.findall(block))
    return paths


def analyze(files: RepoFiles) -> GoAnalysis:
    go_paths = files.with_suffix(".go")
    modules = files.named("go.mod")
    result = GoAnalysis(files_scanned=len(go_paths), packages_scanned=len(modules))
    if not modules:
        return result

    imports = {path: _imports(files.read(path) or "") for path in go_paths}
    for manifest in modules:
        directory = dirname(manifest)
        text = files.read(manifest) or ""
        scope = [p for p in go_paths if is_under(p, directory)]
        used = set().union(*(imports[p] for p in scope)) if scope else set()
        where = "the repo root" if directory == "." else directory
        for module, line in _requirements(text):
            if any(path == module or path.startswith(module + "/") for path in used):
                continue
            result.findings.append(
                Finding(
                    UNUSED_PACKAGE, directory, module, manifest, line,
                    f"{module} is required in {manifest}:{line} and no Go file under {where} imports it or any of its packages. "
                    f"Searched {len(scope)} Go files.",
                    SAFE, "go",
                )
            )
    return result
