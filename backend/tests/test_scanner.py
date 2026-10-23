import json
from pathlib import Path

import pytest

from lopper.scanner import ScanLimitError, scan_path


def write(root: Path, files: dict[str, str]) -> Path:
    for relative, content in files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return root


def pkg(**sections) -> str:
    return json.dumps({"name": "demo", "version": "1.0.0", **sections}, indent=2)


def find(result, type_, item):
    matches = [f for f in result.findings if f.type == type_ and f.item == item]
    return matches[0] if matches else None


# ---------- JavaScript and TypeScript ----------


def test_unused_dependency_is_safe_and_used_one_is_not(tmp_path):
    write(tmp_path, {
        "package.json": pkg(dependencies={"lodash": "^4", "left-pad": "^1", "@scope/ui": "^1"}),
        "src/index.ts": "import get from 'lodash/get';\nimport { Button } from '@scope/ui';\nexport const x = get({}, 'a') && Button;\n",
    })
    result = scan_path(tmp_path)
    unused = find(result, "unused-package", "left-pad")
    assert unused and unused.confidence == "safe"
    assert unused.file_path == "package.json" and unused.line == 6
    assert "No file under the repo root imports 'left-pad'" in unused.evidence
    assert find(result, "unused-package", "lodash") is None
    assert find(result, "unused-package", "@scope/ui") is None


def test_tooling_dev_dependency_is_uncertain_unless_a_script_names_it(tmp_path):
    write(tmp_path, {
        "package.json": pkg(
            scripts={"lint": "eslint .", "build": "tsc"},
            devDependencies={"eslint": "^9", "typescript": "^5", "prettier": "^3", "some-unused-tool": "^1"},
        ),
        "src/a.ts": "export {};\n",
    })
    result = scan_path(tmp_path)
    assert find(result, "unused-dev-dependency", "eslint") is None  # named in scripts
    assert find(result, "unused-dev-dependency", "typescript") is None  # its bin, tsc, is in scripts
    prettier = find(result, "unused-dev-dependency", "prettier")
    assert prettier and prettier.confidence == "uncertain"
    assert find(result, "unused-dev-dependency", "some-unused-tool").confidence == "safe"


def test_a_package_named_in_a_string_is_uncertain_not_safe(tmp_path):
    write(tmp_path, {
        "package.json": pkg(devDependencies={"@google/design.md": "^1"}),
        "scripts/run.ts": "const cli = join('node_modules', '@google', 'design.md', 'dist', 'index.js');\nexport {};\n",
    })
    finding = find(scan_path(tmp_path), "unused-dev-dependency", "@google/design.md")
    assert finding and finding.confidence == "uncertain"
    assert "scripts/run.ts mentions 'design.md' as text" in finding.evidence


def test_types_package_follows_the_package_it_describes(tmp_path):
    write(tmp_path, {
        "package.json": pkg(
            dependencies={"express": "^4"},
            devDependencies={"@types/express": "^4", "@types/node": "^20", "@types/lodash": "^4"},
        ),
        "src/server.ts": "import express from 'express';\nexport const app = express();\n",
    })
    result = scan_path(tmp_path)
    assert find(result, "unused-dev-dependency", "@types/express") is None
    assert find(result, "unused-dev-dependency", "@types/node") is None
    lodash_types = find(result, "unused-dev-dependency", "@types/lodash")
    assert lodash_types and lodash_types.confidence == "uncertain"


def test_monorepo_packages_are_checked_separately(tmp_path):
    write(tmp_path, {
        "package.json": pkg(private=True, workspaces=["packages/*"]),
        "packages/billing/package.json": pkg(name="billing", dependencies={"dayjs": "^1", "uuid": "^9"}),
        "packages/billing/src/format.ts": "import dayjs from 'dayjs';\nexport const day = () => dayjs();\n",
        "packages/auth/package.json": pkg(name="auth", dependencies={"uuid": "^9"}),
        "packages/auth/src/token.ts": "import { v4 } from 'uuid';\nexport const id = v4;\n",
    })
    result = scan_path(tmp_path)
    assert find(result, "unused-package", "dayjs") is None
    uuid_findings = [f for f in result.findings if f.item == "uuid"]
    assert [f.package for f in uuid_findings] == ["packages/billing"]
    assert result.packages_scanned == 3


def test_unused_export_is_found_with_evidence_and_location(tmp_path):
    write(tmp_path, {
        "package.json": pkg(),
        "src/format.ts": "export function formatInvoice() {}\nexport const keep = 1;\nexport interface Shape {}\n",
        "src/main.ts": "import { keep } from './format';\nconsole.log(keep);\n",
    })
    result = scan_path(tmp_path)
    unused = find(result, "unused-export", "formatInvoice")
    assert unused and unused.confidence == "safe"
    assert unused.file_path == "src/format.ts" and unused.line == 1
    assert "no other file mentions it" in unused.evidence
    assert find(result, "unused-export", "Shape").confidence == "safe"
    assert find(result, "unused-export", "keep") is None


def test_export_used_only_in_tests_is_uncertain(tmp_path):
    write(tmp_path, {
        "package.json": pkg(),
        "src/token.ts": "export function parseLegacyToken() {}\n",
        "src/token.test.ts": "import { parseLegacyToken } from './token';\nparseLegacyToken();\n",
    })
    finding = find(scan_path(tmp_path), "unused-export", "parseLegacyToken")
    assert finding and finding.confidence == "uncertain"
    assert "only test files mention it" in finding.evidence


def test_exports_that_a_framework_or_package_entry_can_reach_are_skipped(tmp_path):
    write(tmp_path, {
        "package.json": pkg(main="dist/index.js", dependencies={"next": "^14"}),
        "src/index.ts": "export const publicApi = 1;\n",
        "pages/about.tsx": "export const getServerSideProps = () => ({});\nexport default function About() {}\n",
        "app/page.tsx": "export const metadata = {};\n",
        "vite.config.ts": "export const helper = 1;\n",
        "src/types.d.ts": "export interface Ambient {}\n",
    })
    names = {f.item for f in scan_path(tmp_path).findings if f.type == "unused-export"}
    assert names == set()


def test_namespace_import_makes_an_unused_export_uncertain(tmp_path):
    write(tmp_path, {
        "package.json": pkg(),
        "src/handlers.ts": "export function onCreate() {}\n",
        "src/main.ts": "import * as handlers from './handlers';\nconsole.log(handlers);\n",
    })
    finding = find(scan_path(tmp_path), "unused-export", "onCreate")
    assert finding and finding.confidence == "uncertain"
    assert "namespace or dynamic import" in finding.evidence


def test_unused_import_is_a_report_only_lint_issue(tmp_path):
    write(tmp_path, {
        "package.json": pkg(dependencies={"react": "^18"}),
        "src/App.tsx": "import React from 'react';\nimport { useState, useEffect } from 'react';\nexport const A = () => { useState(); return null; };\n",
    })
    result = scan_path(tmp_path)
    lint = [f for f in result.findings if f.type == "lint-issue"]
    assert [f.item for f in lint] == ["Unused import 'useEffect'"]
    assert lint[0].report_only and lint[0].line == 2


def test_lint_can_be_switched_off(tmp_path):
    write(tmp_path, {"package.json": pkg(), "src/a.ts": "import { x } from './b';\nexport const y = 1;\n"})
    assert not [f for f in scan_path(tmp_path, include_lint=False).findings if f.type == "lint-issue"]


def test_node_modules_and_build_output_are_ignored(tmp_path):
    write(tmp_path, {
        "package.json": pkg(dependencies={"real-dep": "^1"}),
        "node_modules/real-dep/index.js": "module.exports = 1;\n",
        "node_modules/other/package.json": pkg(name="other", dependencies={"ghost": "^1"}),
        "dist/bundle.js": "import 'real-dep';\n",
        "src/a.ts": "export {};\n",
    })
    result = scan_path(tmp_path)
    assert find(result, "unused-package", "real-dep") is not None  # dist/ does not count as a use
    assert find(result, "unused-package", "ghost") is None


# ---------- Python ----------


def test_python_requirements_are_matched_to_import_names(tmp_path):
    write(tmp_path, {
        "requirements.txt": "flask==3.0\nPyYAML>=6\npillow\nrequests\n# comment\n-r other.txt\n",
        "app.py": "import flask\nimport yaml\nfrom PIL import Image\nprint(flask, yaml, Image)\n",
    })
    result = scan_path(tmp_path)
    unused = [f for f in result.findings if f.type == "unused-package"]
    assert [f.item for f in unused] == ["requests"]
    assert unused[0].file_path == "requirements.txt" and unused[0].line == 4 and unused[0].language == "python"


def test_python_dev_requirements_and_pyproject_groups(tmp_path):
    write(tmp_path, {
        "pyproject.toml": (
            '[project]\nname = "x"\ndependencies = ["flask>=3", "stale-lib"]\n'
            '[project.optional-dependencies]\ndev = ["pytest>=8", "unused-dev-lib"]\n'
        ),
        "x/app.py": "import flask\nprint(flask)\n",
    })
    result = scan_path(tmp_path)
    assert find(result, "unused-package", "stale-lib").confidence == "safe"
    assert find(result, "unused-dev-dependency", "pytest").confidence == "uncertain"
    assert find(result, "unused-dev-dependency", "unused-dev-lib").confidence == "safe"
    assert find(result, "unused-package", "flask") is None


def test_python_unused_function_and_class_but_not_decorated_or_private(tmp_path):
    write(tmp_path, {
        "pkg/util.py": (
            "def used(): pass\n"
            "def dead(): pass\n"
            "def _private(): pass\n"
            "class Orphan: pass\n"
            "class Plugin(Base): pass\n"
            "@route('/x')\ndef view(): pass\n"
            "def main(): pass\n"
        ),
        "pkg/run.py": "from pkg.util import used\nused()\n",
        "tests/test_util.py": "from pkg.util import used\n",
    })
    result = scan_path(tmp_path)
    unused = {f.item: f for f in result.findings if f.type == "unused-export"}
    assert set(unused) == {"dead", "Orphan", "Plugin"}
    assert unused["dead"].confidence == "safe"
    assert unused["Plugin"].confidence == "uncertain"


def test_python_function_used_inside_its_own_file_is_not_dead(tmp_path):
    write(tmp_path, {"script.py": "def helper(): pass\ndef dead(): pass\nhelper()\n"})
    names = {f.item for f in scan_path(tmp_path).findings if f.type == "unused-export"}
    assert names == {"dead"}


def test_python_unused_import_is_lint_and_report_only(tmp_path):
    write(tmp_path, {
        "mod.py": "import os\nimport sys\nfrom typing import List\nfrom __future__ import annotations\nprint(sys)\nx: 'List[int]' = []\n",
    })
    lint = [f for f in scan_path(tmp_path).findings if f.type == "lint-issue"]
    assert [f.item for f in lint] == ["Unused import 'os'"]
    assert lint[0].report_only


def test_python_syntax_errors_are_skipped_not_fatal(tmp_path):
    write(tmp_path, {"broken.py": "def (:\n", "ok.py": "import os\n"})
    result = scan_path(tmp_path)
    assert result.files_scanned == 2


def test_python_tool_named_in_config_in_another_folder_is_not_flagged(tmp_path):
    write(tmp_path, {
        "pyproject.toml": '[project]\nname = "x"\ndependencies = []\n[dependency-groups]\ndocs = ["myst-parser", "sphinxcontrib-log-cabinet", "plain-unused"]\n',
        "docs/conf.py": 'extensions = ["myst_parser", "sphinxcontrib.log_cabinet"]\n',
        "x/app.py": "print(1)\n",
    })
    names = {f.item for f in scan_path(tmp_path).findings if f.type == "unused-dev-dependency"}
    assert names == {"plain-unused"}


def test_public_module_of_an_installable_package_is_uncertain(tmp_path):
    write(tmp_path, {
        "pyproject.toml": '[project]\nname = "lib"\ndependencies = []\n',
        "src/lib/__init__.py": "",
        "src/lib/testing.py": "class Result: pass\n",
        "src/lib/_compat.py": "def get_stdout(): pass\n",
        "examples/demo.py": "def helper(): pass\n",
    })
    found = {f.item: f.confidence for f in scan_path(tmp_path).findings if f.type == "unused-export"}
    assert found == {"Result": "uncertain", "get_stdout": "safe", "helper": "safe"}


def test_js_tool_named_in_nested_config_is_not_flagged(tmp_path):
    write(tmp_path, {
        "package.json": pkg(devDependencies={"eslint-plugin-custom": "1", "plain-unused": "1"}),
        "src/.eslintrc.json": '{"plugins": ["eslint-plugin-custom"]}',
        "src/a.ts": "export {};\n",
    })
    names = {f.item for f in scan_path(tmp_path).findings if f.type == "unused-dev-dependency"}
    assert names == {"plain-unused"}


# ---------- Go ----------


def test_go_unused_requirement_but_not_indirect_or_used(tmp_path):
    write(tmp_path, {
        "go.mod": (
            "module example.com/app\n\ngo 1.22\n\nrequire (\n"
            "\tgithub.com/gin-gonic/gin v1.9.1\n"
            "\tgithub.com/stale/lib v1.0.0\n"
            "\tgolang.org/x/text v0.14.0 // indirect\n)\n"
        ),
        "main.go": 'package main\n\nimport (\n\t"fmt"\n\t"github.com/gin-gonic/gin/binding"\n)\n\nfunc main() { fmt.Println(binding.JSON) }\n',
    })
    result = scan_path(tmp_path)
    unused = [f for f in result.findings if f.type == "unused-package"]
    assert [f.item for f in unused] == ["github.com/stale/lib"]
    assert unused[0].line == 7 and unused[0].language == "go"
    assert result.languages == ["go"]


# ---------- Whole scan ----------


def test_scan_never_modifies_the_folder(tmp_path):
    write(tmp_path, {
        "package.json": pkg(dependencies={"left-pad": "^1"}),
        "src/a.ts": "import { z } from './b';\nexport function dead() {}\n",
        "requirements.txt": "requests\n",
    })
    before = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    scan_path(tmp_path)
    after = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    assert before == after


def test_findings_are_ordered_and_counted(tmp_path):
    write(tmp_path, {
        "package.json": pkg(dependencies={"a-dep": "1"}, devDependencies={"b-dev": "1"}),
        "src/a.ts": "import { z } from './nothing';\nexport function dead() {}\n",
    })
    result = scan_path(tmp_path)
    assert [f.type for f in result.findings] == ["unused-package", "unused-dev-dependency", "unused-export", "lint-issue"]
    assert result.counts() == {"unused-package": 1, "unused-dev-dependency": 1, "unused-export": 1, "lint-issue": 1}
    assert result.to_dict()["languages"] == ["javascript"]


def test_oversized_repos_are_refused(tmp_path):
    write(tmp_path, {f"f{i}.js": "" for i in range(5)})
    with pytest.raises(ScanLimitError):
        scan_path(tmp_path, max_files=3)


def test_symlinks_are_not_followed(tmp_path):
    outside = tmp_path / "outside"
    write(outside, {"secret.js": "import 'leaked-dep';\n"})
    repo = tmp_path / "repo"
    write(repo, {"package.json": pkg(dependencies={"leaked-dep": "1"})})
    try:
        (repo / "link").symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("symlinks need extra privileges on this machine")
    assert find(scan_path(repo), "unused-package", "leaked-dep") is not None


def test_not_a_folder(tmp_path):
    with pytest.raises(NotADirectoryError):
        scan_path(tmp_path / "missing")
