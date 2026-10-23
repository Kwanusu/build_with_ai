"""JavaScript and TypeScript: unused dependencies, unused dev dependencies, unused exports and unused imports.

The analysis is name-based and deliberately conservative. When something could be used in a way we
can't see (a tool config, a framework convention, a namespace import), we still report it but mark it
"uncertain" so a person looks before ticking it. We never run the code we scan.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

from .models import (
    LINT_ISSUE, SAFE, UNCERTAIN, UNUSED_DEV_DEPENDENCY, UNUSED_EXPORT, UNUSED_PACKAGE, Finding,
)
from .walk import RepoFiles, dirname, is_test_path, is_under

JS_SUFFIXES = (".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".mts", ".cts")

NODE_BUILTINS = frozenset(
    "assert async_hooks buffer child_process cluster console constants crypto dgram diagnostics_channel dns domain "
    "events fs http http2 https inspector module net os path perf_hooks process punycode querystring readline repl "
    "stream string_decoder sys timers tls trace_events tty url util v8 vm wasi worker_threads zlib".split()
)

FROM_RE = re.compile(r"""\bfrom\s*(['"])([^'"\n]+)\1""")
SIDE_EFFECT_RE = re.compile(r"""^[ \t]*import\s*(['"])([^'"\n]+)\1""", re.M)
CALL_RE = re.compile(
    r"""\b(?:require|import|require\.resolve|(?:jest|vi)\.(?:mock|doMock|unmock|requireActual|importActual))"""
    r"""\s*\(\s*(['"])([^'"\n]+)\1"""
)
TOKEN_RE = re.compile(r"[A-Za-z_$][\w$]*")

EXPORT_DECL_RE = re.compile(
    r"^[ \t]*export[ \t]+(?:declare[ \t]+)?(?:async[ \t]+)?"
    r"(?:const[ \t]+enum|function\*?|abstract[ \t]+class|class|const|let|var|enum|interface|type)[ \t]+([A-Za-z_$][\w$]*)",
    re.M,
)
EXPORT_LIST_RE = re.compile(r"""^[ \t]*export[ \t]+(?:type[ \t]+)?\{([^}]*)\}[ \t]*(from[ \t]*['"][^'"]+['"])?""", re.M)
IMPORT_STMT_RE = re.compile(
    r"""^[ \t]*import[ \t]+(?!\()(?:type[ \t]+)?([\w$]+)?[ \t]*,?[ \t]*(?:\*[ \t]+as[ \t]+([\w$]+)|\{([^}]*)\})?[ \t]*from[ \t]*['"][^'"]+['"]""",
    re.M,
)
NAMESPACE_OR_DYNAMIC_RE = re.compile(
    r"""(?:import\s*\*\s*as\s+[\w$]+\s+from\s*|import\s*\(\s*|require\s*\(\s*)(['"])(\.{1,2}/[^'"\n]+)\1"""
)

# Tools that are loaded by their own config or from the command line, so "no import" doesn't mean unused.
TOOLING_PREFIXES = (
    "eslint", "@eslint/", "@typescript-eslint/", "prettier", "typescript", "@babel/", "babel-", "jest", "@jest/", "ts-jest",
    "ts-node", "tsx", "vitest", "@vitest/", "webpack", "vite", "@vitejs/", "rollup", "esbuild", "postcss", "tailwindcss",
    "autoprefixer", "husky", "lint-staged", "nodemon", "concurrently", "cross-env", "rimraf", "turbo", "nx", "@nx/", "lerna",
    "@changesets/", "playwright", "@playwright/", "cypress", "storybook", "@storybook/", "stylelint", "commitlint",
    "@commitlint/", "npm-run-all", "tsup", "swc", "@swc/", "sass", "less", "ts-loader", "babel-loader", "css-loader",
    "style-loader", "mocha", "chai", "sinon", "nyc", "c8", "supertest", "rollup-plugin-", "vite-plugin-", "@types/",
    "@testing-library/", "jsdom", "happy-dom", "msw", "knip", "depcheck", "ts-prune", "size-limit", "@size-limit/",
)

# Packages the runtime or bundler pulls in without an import in our code.
IMPLICIT_RUNTIME = frozenset({"tslib", "core-js", "regenerator-runtime", "@babel/runtime", "source-map-support", "sharp"})

BIN_ALIASES = {
    "typescript": ("tsc", "tsserver"),
    "@babel/cli": ("babel",),
    "@babel/core": ("babel",),
    "webpack-cli": ("webpack",),
    "npm-run-all": ("run-s", "run-p", "npm-run-all"),
    "npm-run-all2": ("run-s", "run-p", "npm-run-all"),
    "@playwright/test": ("playwright",),
    "@angular/cli": ("ng",),
    "@nestjs/cli": ("nest",),
    "lint-staged": ("lint-staged",),
    "@commitlint/cli": ("commitlint",),
    "@changesets/cli": ("changeset",),
    "ts-jest": ("jest",),
    "sass": ("sass",),
    "@storybook/cli": ("storybook",),
}

FRAMEWORKS_WITH_APP_DIR = ("next", "nuxt", "astro", "@sveltejs/kit", "@remix-run/react", "@remix-run/node")
CONVENTION_DIRS = frozenset({"pages", "routes", "stories", "storybook", "__mocks__", "migrations", "seeds", "fixtures"})
CONVENTION_NAMES = frozenset(
    {
        "page", "layout", "route", "loading", "error", "not-found", "middleware", "template", "default", "global-error",
        "instrumentation", "sitemap", "robots", "manifest", "opengraph-image", "twitter-image", "icon", "apple-icon",
    }
)

LOCK_FILES = frozenset({"package-lock.json", "pnpm-lock.yaml", "yarn.lock", "npm-shrinkwrap.json", "composer.lock"})

CONFIG_NAME_RE = re.compile(
    r"^(\..+|.*config.*|tsconfig.*\.json|Dockerfile.*|Makefile|Procfile|.*\.ya?ml|.*\.toml|.*rc)$", re.I
)


@dataclass
class Package:
    directory: str
    manifest_path: str
    manifest_text: str
    data: dict
    name: str | None = None
    dependencies: list[str] = field(default_factory=list)
    dev_dependencies: list[str] = field(default_factory=list)


@dataclass
class JsAnalysis:
    findings: list[Finding] = field(default_factory=list)
    files_scanned: int = 0
    packages_scanned: int = 0


def package_name(specifier: str) -> str | None:
    """The npm package a module specifier refers to, or None for relative paths, built-ins and aliases."""
    if not specifier or specifier[0] in ".#~/" or specifier.startswith(("@/", "~", "node:", "bun:", "data:", "http:", "https:")):
        return None
    parts = specifier.split("/")
    if specifier.startswith("@"):
        if len(parts) < 2 or not parts[1]:
            return None
        return f"{parts[0]}/{parts[1]}"
    name = parts[0]
    return None if name in NODE_BUILTINS else name


def extract_imports(text: str) -> set[str]:
    found: set[str] = set()
    for regex in (FROM_RE, SIDE_EFFECT_RE, CALL_RE):
        for match in regex.finditer(text):
            name = package_name(match.group(2))
            if name:
                found.add(name)
    return found


def _line_of(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def _entry_stems(package: Package) -> set[str]:
    """Paths (without extension) that a package publishes as its public surface."""
    values: list[str] = []

    def walk(node: object) -> None:
        if isinstance(node, str):
            values.append(node)
        elif isinstance(node, dict):
            for child in node.values():
                walk(child)
        elif isinstance(node, list):
            for child in node:
                walk(child)

    for key in ("main", "module", "types", "typings", "browser", "bin", "exports", "source"):
        if key in package.data:
            walk(package.data[key])
    stems = set()
    for value in values:
        cleaned = value.removeprefix("./")
        stems.add(re.sub(r"\.(d\.)?[cm]?[jt]sx?$", "", cleaned))
    return stems


def _is_published(package: Package) -> bool:
    return any(key in package.data for key in ("main", "module", "types", "typings", "exports", "bin"))


def _stem(path: str) -> str:
    return re.sub(r"\.[cm]?[jt]sx?$", "", path)


def _mentions(refs: str, name: str) -> bool:
    return re.search(rf"(?<![\w@/.-]){re.escape(name)}(?![\w-])", refs) is not None


def _is_tooling(name: str) -> bool:
    return name.startswith(TOOLING_PREFIXES)


def _config_text(files: RepoFiles, package: Package) -> str:
    """Scripts and tool config for one package: the places a tool can be named without an import."""
    skip_keys = {"dependencies", "devDependencies", "peerDependencies", "optionalDependencies"}
    chunks = [json.dumps({k: v for k, v in package.data.items() if k not in skip_keys})]
    directory = package.directory
    prefix = "" if directory == "." else directory + "/"
    for path in files.paths:
        if not path.startswith(prefix):
            continue
        relative = path[len(prefix):]
        top_level = "/" not in relative
        in_ci = relative.startswith((".github/", ".husky/", ".circleci/", ".gitlab/"))
        name = relative.rsplit("/", 1)[-1]
        # Config files in sub-folders count too (an .eslintrc.json in src/, a workflow in a nested package).
        deep_config = path.endswith((".json", ".yml", ".yaml", ".toml")) and name not in LOCK_FILES
        if not (top_level or in_ci or deep_config):
            continue
        if path.endswith(JS_SUFFIXES) and not CONFIG_NAME_RE.match(name):
            continue
        if path.endswith("package.json") or not (CONFIG_NAME_RE.match(name) or in_ci or deep_config):
            continue
        text = files.read(path)
        if text and len(text) < 200_000:
            chunks.append(text)
    return "\n".join(chunks)


def _load_packages(files: RepoFiles) -> list[Package]:
    packages = []
    for manifest in files.named("package.json"):
        text = files.read(manifest)
        if text is None:
            continue
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            continue
        if not isinstance(data, dict):
            continue
        package = Package(directory=dirname(manifest), manifest_path=manifest, manifest_text=text, data=data)
        package.name = data.get("name") if isinstance(data.get("name"), str) else None
        for key in ("dependencies", "optionalDependencies"):
            section = data.get(key)
            if isinstance(section, dict):
                package.dependencies.extend(section)
        section = data.get("devDependencies")
        if isinstance(section, dict):
            package.dev_dependencies.extend(section)
        packages.append(package)
    return packages


def _declaration_line(package: Package, section: str, name: str) -> int | None:
    start = package.manifest_text.find(f'"{section}"')
    index = package.manifest_text.find(f'"{name}"', max(start, 0))
    return _line_of(package.manifest_text, index) if index >= 0 else None


def analyze(files: RepoFiles, include_lint: bool = True) -> JsAnalysis:
    packages = _load_packages(files)
    js_paths = files.with_suffix(*JS_SUFFIXES)
    result = JsAnalysis(files_scanned=len(js_paths), packages_scanned=len(packages))
    if not packages and not js_paths:
        return result

    texts: dict[str, str] = {}
    for path in js_paths:
        text = files.read(path)
        if text is not None:
            texts[path] = text
    imports = {path: extract_imports(text) for path, text in texts.items()}

    uses_app_dir = any(
        any(dep in FRAMEWORKS_WITH_APP_DIR for dep in package.dependencies + package.dev_dependencies) for package in packages
    )

    for package in packages:
        result.findings.extend(_unused_dependencies(files, package, texts, imports))
    result.findings.extend(_unused_exports(files, packages, texts, js_paths, uses_app_dir))
    if include_lint:
        result.findings.extend(_unused_imports(texts))
    return result


def _unused_dependencies(
    files: RepoFiles, package: Package, texts: dict[str, str], imports: dict[str, set[str]]
) -> list[Finding]:
    scope = [path for path in texts if is_under(path, package.directory)]
    used: set[str] = set()
    for path in scope:
        used |= imports[path]
    refs = _config_text(files, package)
    where = "the repo root" if package.directory == "." else package.directory
    config_count = refs.count("\n") + 1
    findings: list[Finding] = []

    def check(names: list[str], section: str, kind: str) -> None:
        for name in names:
            if name in used or _mentions(refs, name):
                continue
            if any(_mentions(refs, alias) for alias in BIN_ALIASES.get(name, ())):
                continue
            if name.startswith("@types/"):
                base = name.removeprefix("@types/")
                base = base.replace("__", "/", 1) if "__" in base else base
                if base == "node" or base in used or (f"@{base}" in used):
                    continue
                evidence = (
                    f"Nothing under {where} imports '{base}', the package '{name}' describes. "
                    f"Searched {len(scope)} source files."
                )
                findings.append(
                    Finding(kind, package.directory, name, package.manifest_path, _declaration_line(package, section, name),
                            evidence, UNCERTAIN, "javascript")
                )
                continue
            tooling = _is_tooling(name) or name in IMPLICIT_RUNTIME
            evidence = (
                f"No file under {where} imports '{name}', and no script or config file mentions it. "
                f"Searched {len(scope)} source files and about {config_count} lines of config and scripts."
            )
            if tooling:
                evidence += " It looks like tooling that a config file can load by name, so check before removing it."
            # A package can be loaded by path or by a string (a bin script, a require.resolve, a plugin name).
            tail = name.rsplit("/", 1)[-1]
            text_hit = next((p for p in scope if len(tail) >= 4 and tail in texts[p]), None)
            if text_hit:
                evidence += f" {text_hit} mentions '{tail}' as text, which can load the package without an import."
            findings.append(
                Finding(kind, package.directory, name, package.manifest_path, _declaration_line(package, section, name),
                        evidence, UNCERTAIN if (tooling or text_hit) else SAFE, "javascript")
            )

    check(package.dependencies, "dependencies", UNUSED_PACKAGE)
    check(package.dev_dependencies, "devDependencies", UNUSED_DEV_DEPENDENCY)
    return findings


def _owning_package(path: str, packages: list[Package]) -> Package | None:
    best: Package | None = None
    for package in packages:
        if is_under(path, package.directory) and (best is None or len(package.directory) > len(best.directory)):
            best = package
    return best


def _unused_exports(
    files: RepoFiles, packages: list[Package], texts: dict[str, str], js_paths: list[str], uses_app_dir: bool
) -> list[Finding]:
    index: dict[str, set[str]] = {}
    for path, text in texts.items():
        for token in set(TOKEN_RE.findall(text)):
            index.setdefault(token, set()).add(path)

    indirect_stems: set[str] = set()
    for text in texts.values():
        for match in NAMESPACE_OR_DYNAMIC_RE.finditer(text):
            indirect_stems.add(match.group(2).rstrip("/").rsplit("/", 1)[-1].rsplit(".", 1)[0])

    entry_stems: dict[str, set[str]] = {p.directory: _entry_stems(p) for p in packages}
    published = {p.directory: _is_published(p) for p in packages}
    convention_dirs = CONVENTION_DIRS | ({"app"} if uses_app_dir else set())
    total_files = len(texts)
    total_packages = len(packages)
    findings: list[Finding] = []

    for path, text in texts.items():
        name = path.rsplit("/", 1)[-1]
        stem_name = name.split(".", 1)[0]
        if (
            path.endswith((".d.ts", ".d.mts", ".d.cts"))
            or is_test_path(path)
            or ".config." in name
            or ".stories." in name
            or stem_name in CONVENTION_NAMES
            or any(part in convention_dirs for part in path.split("/")[:-1])
        ):
            continue
        owner = _owning_package(path, packages)
        if owner is not None:
            if _stem(path) in {os_join(owner.directory, stem) for stem in entry_stems[owner.directory]}:
                continue
            if published[owner.directory] and stem_name == "index":
                continue
        if stem_name == "index" and re.search(r"^[ \t]*export[^\n]*\bfrom\b", text, re.M):
            continue

        exported: list[tuple[str, int]] = []
        for match in EXPORT_DECL_RE.finditer(text):
            exported.append((match.group(1), _line_of(text, match.start())))
        for match in EXPORT_LIST_RE.finditer(text):
            if match.group(2):
                continue
            for part in match.group(1).split(","):
                part = re.sub(r"^type\s+", "", part.strip())
                if not part:
                    continue
                local = re.split(r"\s+as\s+", part)[-1].strip()
                if local and local != "default":
                    exported.append((local, _line_of(text, match.start())))

        language = "typescript" if path.endswith((".ts", ".tsx", ".mts", ".cts")) else "javascript"
        package_dir = owner.directory if owner else "."
        for item, line in exported:
            others = index.get(item, set()) - {path}
            outside_tests = {other for other in others if not is_test_path(other)}
            if outside_tests:
                continue
            searched = f"Searched {total_files:,} source files across {total_packages} package{'s' if total_packages != 1 else ''}."
            if others:
                evidence = f"{item} is exported from {path}:{line} and only test files mention it, such as {sorted(others)[0]}. {searched}"
                confidence = UNCERTAIN
            else:
                evidence = f"{item} is exported from {path}:{line} and no other file mentions it. {searched}"
                confidence = SAFE
                if stem_name in indirect_stems:
                    evidence += f" {name} is also loaded with a namespace or dynamic import, which can reach it by name."
                    confidence = UNCERTAIN
            findings.append(Finding(UNUSED_EXPORT, package_dir, item, path, line, evidence, confidence, language))
    return findings


def os_join(directory: str, relative: str) -> str:
    return relative if directory == "." else f"{directory}/{relative}"


def _unused_imports(texts: dict[str, str]) -> list[Finding]:
    findings: list[Finding] = []
    for path, text in texts.items():
        if path.endswith((".d.ts", ".d.mts", ".d.cts")):
            continue
        body = IMPORT_STMT_RE.sub("", text)
        is_jsx = path.endswith((".jsx", ".tsx"))
        for match in IMPORT_STMT_RE.finditer(text):
            bindings: list[str] = []
            if match.group(1):
                bindings.append(match.group(1))
            if match.group(2):
                bindings.append(match.group(2))
            if match.group(3):
                for part in match.group(3).split(","):
                    part = re.sub(r"^type\s+", "", part.strip())
                    if part:
                        bindings.append(re.split(r"\s+as\s+", part)[-1].strip())
            for binding in bindings:
                if is_jsx and binding == "React":
                    continue
                if re.search(rf"(?<![\w$]){re.escape(binding)}(?![\w$])", body):
                    continue
                line = _line_of(text, match.start())
                findings.append(
                    Finding(
                        LINT_ISSUE, ".", f"Unused import '{binding}'", path, line,
                        f"'{binding}' is imported on line {line} of {path} and is not used anywhere else in the file.",
                        SAFE, "typescript" if path.endswith((".ts", ".tsx", ".mts", ".cts")) else "javascript",
                        report_only=True,
                    )
                )
    return findings
