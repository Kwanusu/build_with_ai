"""Turning ticked findings into file edits for a pull request.

Text in, text out: nothing here touches the network or runs anyone's code. Each edit checks that the line is still
what the scan saw, and if it isn't (the file moved on since the scan) the finding is left out with a reason
instead of guessed at.

What it can change today:
  - an unused dependency or dev dependency: its line in package.json is removed
  - an unused export in JavaScript or TypeScript: the `export` keyword is dropped from the declaration
Everything else (Python, Go, export lists, lint issues) is left for a person, and the reason is reported.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from dataclasses import dataclass, field

JS_LANGUAGES = ("javascript", "typescript")

# A line of package.json like:   "left-pad": "^1.3.0",
DEPENDENCY_LINE = re.compile(r'^\s*"((?:[^"\\]|\\.)*)"\s*:\s*"(?:[^"\\]|\\.)*"\s*(,?)\s*$')


@dataclass
class Plan:
    files: dict[str, str] = field(default_factory=dict)  # path -> the new text
    applied: list[dict] = field(default_factory=list)  # what we changed
    skipped: list[dict] = field(default_factory=list)  # what we left alone, and why

    @property
    def touches_package_json(self) -> bool:
        return any(path.rsplit("/", 1)[-1] == "package.json" for path in self.files)


def _eol(line: str) -> str:
    return line[len(line.rstrip("\r\n")):]


def remove_dependency(lines: list[str], line_number: int | None, name: str) -> str | None:
    """Delete the package.json line for `name`. Returns None on success, or why it wasn't done."""
    index = (line_number or 0) - 1
    if not 0 <= index < len(lines):
        return "package.json has changed since the scan, so the line isn't there any more."
    match = DEPENDENCY_LINE.match(lines[index].rstrip("\r\n"))
    if not match or json.loads(f'"{match.group(1)}"') != name:
        return "package.json has changed since the scan, so Lopper left it alone."
    had_comma = match.group(2) == ","
    del lines[index]
    if not had_comma and index > 0 and lines[index - 1].rstrip().endswith(","):
        # That was the last entry, so the one before it must not end in a comma any more.
        previous = lines[index - 1]
        lines[index - 1] = previous.rstrip()[:-1] + _eol(previous)
    return None


def drop_export_keyword(lines: list[str], line_number: int | None, name: str) -> str | None:
    """Turn `export function name` into `function name`. Returns None on success, or why it wasn't done."""
    index = (line_number or 0) - 1
    if not 0 <= index < len(lines):
        return "The file has changed since the scan, so the line isn't there any more."
    pattern = re.compile(
        r"^(\s*)export\s+((?:declare\s+|async\s+|abstract\s+|const\s+)*(?:function\s*\*?|const|let|var|class|interface|type|enum)\s+"
        + re.escape(name)
        + r"\b.*)$",
        re.S,
    )
    match = pattern.match(lines[index])
    if not match:
        return "This export is in an export list, or written in a way Lopper doesn't change on its own. Remove it by hand."
    lines[index] = match.group(1) + match.group(2)
    return None


def _describe(finding: dict) -> str:
    if finding["type"] == "unused-export":
        return f"Stop exporting {finding['item']}"
    kind = "dev dependencies" if finding["type"] == "unused-dev-dependency" else "dependencies"
    return f"Remove {finding['item']} from {kind}"


def plan_changes(findings: list[dict], read: Callable[[str], str | None]) -> Plan:
    """Work out the edits for these ticked findings. `read(path)` gives a file's current text, or None if it isn't there."""
    plan = Plan()
    by_file: dict[str, list[dict]] = {}

    def skip(finding: dict, reason: str) -> None:
        plan.skipped.append({"id": finding["id"], "item": finding["item"], "type": finding["type"], "reason": reason})

    for finding in findings:
        if finding.get("report_only") or finding["type"] == "lint-issue":
            skip(finding, "Lint issues are report only.")
        elif finding["language"] not in JS_LANGUAGES:
            skip(finding, "Lopper only edits JavaScript and TypeScript projects for now.")
        elif finding["type"] != "unused-export" and finding["file_path"].rsplit("/", 1)[-1] != "package.json":
            skip(finding, "Lopper only removes dependencies listed in package.json for now.")
        else:
            by_file.setdefault(finding["file_path"], []).append(finding)

    for path, items in by_file.items():
        text = read(path)
        if text is None:
            for finding in items:
                skip(finding, "The file isn't on the default branch any more.")
            continue
        lines = text.splitlines(keepends=True)
        # Bottom to top, so removing a line never moves the lines still to be edited.
        for finding in sorted(items, key=lambda f: f["line"] or 0, reverse=True):
            if finding["type"] == "unused-export":
                problem = drop_export_keyword(lines, finding["line"], finding["item"])
            else:
                problem = remove_dependency(lines, finding["line"], finding["item"])
            if problem:
                skip(finding, problem)
            else:
                plan.applied.append(
                    {"id": finding["id"], "item": finding["item"], "type": finding["type"], "file_path": path,
                     "summary": _describe(finding), "confidence": finding["confidence"]}
                )
        new_text = "".join(lines)
        if new_text != text:
            plan.files[path] = new_text
    plan.applied.sort(key=lambda a: a["id"])
    plan.skipped.sort(key=lambda s: s["id"])
    return plan


def describe_pull_request(repo: str, plan: Plan) -> tuple[str, str]:
    """The pull request's title and description."""
    count = len(plan.applied)
    title = f"Remove {count} unused item{'s' if count != 1 else ''} found by Lopper"
    lines = [
        f"Lopper scanned `{repo}` and found items that nothing uses. A person ticked these and asked for this pull request.",
        "",
        "## Changes",
        "",
    ]
    for change in plan.applied:
        note = " (needs a closer look: Lopper wasn't certain)" if change["confidence"] == "uncertain" else ""
        lines.append(f"- {change['summary']} (`{change['file_path']}`){note}")
    if plan.touches_package_json:
        lines += ["", "Lock files aren't updated. Run your install command (`npm install`, `yarn` or `pnpm install`) to refresh them."]
    if plan.skipped:
        lines += ["", "## Left for you", ""]
        lines += [f"- `{s['item']}`: {s['reason']}" for s in plan.skipped]
    lines += [
        "",
        "Lopper reads code and never runs it. Please check the build and tests before merging.",
        "",
        "Opened by Lopper.",
    ]
    return title, "\n".join(lines)
