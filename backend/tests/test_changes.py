import json

from lopper.changes import describe_pull_request, plan_changes

PACKAGE_JSON = """{
  "name": "demo",
  "dependencies": {
    "left-pad": "^1.3.0",
    "react": "^19.0.0",
    "lodash": "^4.0.0"
  },
  "devDependencies": {
    "prettier": "^3.0.0"
  }
}
"""

COMPONENT = "import x from 'y';\nexport function formatInvoice() {}\nexport const keep = 1;\nexport { a, b };\n"


def finding(id, type, item, file_path, line, **extra):
    return {"id": id, "type": type, "item": item, "file_path": file_path, "line": line, "language": "javascript",
            "confidence": "safe", "report_only": False, **extra}


def read_from(files):
    return files.get


def test_an_unused_dependency_line_is_removed_and_the_json_stays_valid():
    plan = plan_changes([finding(1, "unused-package", "left-pad", "package.json", 4)], read_from({"package.json": PACKAGE_JSON}))
    assert plan.skipped == []
    new = plan.files["package.json"]
    assert '"left-pad"' not in new and '"react"' in new
    assert json.loads(new)["dependencies"] == {"react": "^19.0.0", "lodash": "^4.0.0"}
    # Only that one line is different, so the diff is one deleted line.
    assert new.count("\n") == PACKAGE_JSON.count("\n") - 1


def test_removing_the_last_entry_takes_the_comma_off_the_one_before():
    plan = plan_changes([finding(1, "unused-package", "lodash", "package.json", 6)], read_from({"package.json": PACKAGE_JSON}))
    assert json.loads(plan.files["package.json"])["dependencies"] == {"left-pad": "^1.3.0", "react": "^19.0.0"}


def test_removing_the_only_entry_leaves_an_empty_block():
    plan = plan_changes(
        [finding(1, "unused-dev-dependency", "prettier", "package.json", 9)], read_from({"package.json": PACKAGE_JSON})
    )
    assert json.loads(plan.files["package.json"])["devDependencies"] == {}


def test_several_removals_from_one_file_all_land():
    findings = [
        finding(1, "unused-package", "left-pad", "package.json", 4),
        finding(2, "unused-package", "lodash", "package.json", 6),
        finding(3, "unused-dev-dependency", "prettier", "package.json", 9),
    ]
    plan = plan_changes(findings, read_from({"package.json": PACKAGE_JSON}))
    assert plan.skipped == []
    data = json.loads(plan.files["package.json"])
    assert data["dependencies"] == {"react": "^19.0.0"} and data["devDependencies"] == {}


def test_windows_line_endings_are_kept():
    text = PACKAGE_JSON.replace("\n", "\r\n")
    plan = plan_changes([finding(1, "unused-package", "lodash", "package.json", 6)], read_from({"package.json": text}))
    new = plan.files["package.json"]
    assert "\n" not in new.replace("\r\n", "") and json.loads(new)["dependencies"] == {"left-pad": "^1.3.0", "react": "^19.0.0"}


def test_a_package_json_that_changed_since_the_scan_is_left_alone():
    # The scan saw left-pad on line 4, but a new line was added above it.
    moved = PACKAGE_JSON.replace('  "name": "demo",\n', '  "name": "demo",\n  "private": true,\n')
    plan = plan_changes([finding(1, "unused-package", "left-pad", "package.json", 4)], read_from({"package.json": moved}))
    assert plan.files == {} and plan.applied == []
    assert "changed since the scan" in plan.skipped[0]["reason"]


def test_an_unused_export_stops_being_exported_and_nothing_else_changes():
    plan = plan_changes([finding(1, "unused-export", "formatInvoice", "src/a.ts", 2, language="typescript")], read_from({"src/a.ts": COMPONENT}))
    assert plan.files["src/a.ts"] == "import x from 'y';\nfunction formatInvoice() {}\nexport const keep = 1;\nexport { a, b };\n"
    assert plan.applied[0]["summary"] == "Stop exporting formatInvoice"


def test_exports_in_a_list_or_with_another_name_are_left_for_a_person():
    findings = [
        finding(1, "unused-export", "a", "src/a.ts", 4, language="typescript"),
        finding(2, "unused-export", "formatInvoice", "src/a.ts", 3, language="typescript"),
    ]
    plan = plan_changes(findings, read_from({"src/a.ts": COMPONENT}))
    assert plan.files == {} and [s["id"] for s in plan.skipped] == [1, 2]


def test_other_languages_lint_issues_and_other_manifests_are_left_out_with_a_reason():
    findings = [
        finding(1, "unused-package", "requests", "requirements.txt", 2, language="python"),
        finding(2, "lint-issue", "Unused import 'x'", "src/a.ts", 1, report_only=True),
        finding(3, "unused-package", "serde", "Cargo.toml", 5),
    ]
    plan = plan_changes(findings, read_from({}))
    assert plan.files == {} and plan.applied == []
    assert [s["id"] for s in plan.skipped] == [1, 2, 3]
    assert "JavaScript and TypeScript" in plan.skipped[0]["reason"] and "report only" in plan.skipped[1]["reason"]


def test_a_file_that_is_gone_is_skipped():
    plan = plan_changes([finding(1, "unused-export", "x", "src/gone.ts", 1)], read_from({}))
    assert "isn't on the default branch" in plan.skipped[0]["reason"]


def test_the_pull_request_says_what_changed_what_was_left_and_that_lock_files_need_refreshing():
    findings = [
        finding(1, "unused-package", "left-pad", "package.json", 4, confidence="uncertain"),
        finding(2, "unused-package", "requests", "requirements.txt", 2, language="python"),
    ]
    plan = plan_changes(findings, read_from({"package.json": PACKAGE_JSON}))
    title, body = describe_pull_request("acme/web", plan)
    assert title == "Remove 1 unused item found by Lopper"
    assert "Remove left-pad from dependencies (`package.json`) (needs a closer look" in body
    assert "Lock files aren't updated" in body and "## Left for you" in body and "`requests`" in body
