from __future__ import annotations

from dataclasses import asdict, dataclass, field

UNUSED_PACKAGE = "unused-package"
UNUSED_EXPORT = "unused-export"
UNUSED_DEV_DEPENDENCY = "unused-dev-dependency"
LINT_ISSUE = "lint-issue"

FINDING_TYPES = (UNUSED_PACKAGE, UNUSED_EXPORT, UNUSED_DEV_DEPENDENCY, LINT_ISSUE)

SAFE = "safe"
UNCERTAIN = "uncertain"


@dataclass(frozen=True)
class Finding:
    """One thing Lopper noticed, with the evidence behind it.

    `confidence` is "safe" when we found no use anywhere we looked, and "uncertain" when
    something (a test, a tool config, a framework convention) means a person should look.
    Lint issues are always `report_only`.
    """

    type: str
    package: str
    item: str
    file_path: str
    line: int | None
    evidence: str
    confidence: str
    language: str
    report_only: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ScanResult:
    findings: list[Finding] = field(default_factory=list)
    files_scanned: int = 0
    packages_scanned: int = 0
    languages: list[str] = field(default_factory=list)

    def counts(self) -> dict[str, int]:
        counts = {kind: 0 for kind in FINDING_TYPES}
        for finding in self.findings:
            counts[finding.type] += 1
        return counts

    def to_dict(self) -> dict:
        return {
            "files_scanned": self.files_scanned,
            "packages_scanned": self.packages_scanned,
            "languages": self.languages,
            "counts": self.counts(),
            "findings": [finding.to_dict() for finding in self.findings],
        }
