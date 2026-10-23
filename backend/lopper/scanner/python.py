"""Python: unused requirements, unused public functions and classes, and unused imports.

Python is parsed with `ast`, so it never imports or runs the code it scans.
"""

from __future__ import annotations

import ast
import re
import tomllib
from dataclasses import dataclass, field

from .models import LINT_ISSUE, SAFE, UNCERTAIN, UNUSED_DEV_DEPENDENCY, UNUSED_EXPORT, UNUSED_PACKAGE, Finding
from .walk import RepoFiles, dirname, is_test_path, is_under

# Distribution names whose import name differs from the name you install.
IMPORT_NAMES = {
    "pyyaml": "yaml", "pillow": "PIL", "scikit-learn": "sklearn", "scikit-image": "skimage", "opencv-python": "cv2",
    "opencv-python-headless": "cv2", "beautifulsoup4": "bs4", "python-dateutil": "dateutil", "python-dotenv": "dotenv",
    "pyjwt": "jwt", "protobuf": "google", "psycopg2-binary": "psycopg2", "psycopg-binary": "psycopg",
    "psycopg-pool": "psycopg_pool", "attrs": "attr", "msgpack-python": "msgpack", "pymongo": "pymongo",
    "python-multipart": "multipart", "typing-extensions": "typing_extensions", "pytest-asyncio": "pytest_asyncio",
    "flask-cors": "flask_cors", "flask-sqlalchemy": "flask_sqlalchemy", "djangorestframework": "rest_framework",
    "django-cors-headers": "corsheaders", "google-cloud-storage": "google", "pycryptodome": "Crypto",
    "pyserial": "serial", "pywin32": "win32api", "setuptools": "setuptools", "ruamel-yaml": "ruamel",
    "markdown": "markdown", "pytz": "pytz", "python-jose": "jose", "pyopenssl": "OpenSSL", "gitpython": "git",
    "scapy": "scapy", "lxml": "lxml", "redis": "redis", "celery": "celery",
}

TOOLING_NAMES = frozenset(
    {
        "pytest", "ruff", "black", "flake8", "mypy", "isort", "pylint", "coverage", "tox", "nox", "pre-commit", "gunicorn",
        "uvicorn", "hypercorn", "waitress", "setuptools", "wheel", "pip", "build", "twine", "ipython", "jupyter", "pyright",
        "bandit", "pip-tools", "hatchling", "poetry-core", "flit-core", "sphinx", "mkdocs", "alembic", "honcho", "supervisor",
        "uwsgi", "daphne", "pyinstaller", "cython", "codecov", "pytest-cov", "mypy-extensions", "autopep8", "yapf",
    }
)
TOOLING_PREFIXES = (
    "pytest-", "flake8-", "sphinx-", "sphinxcontrib-", "mkdocs-", "types-", "pylint-", "black-", "mypy-", "django-debug",
    "ruff-", "tox-", "nox-", "pre-commit", "myst-", "furo", "pallets-sphinx",
)

REQ_RE = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)")
IGNORED_PUBLIC_NAMES = frozenset({"main", "app", "create_app", "handler", "lambda_handler", "setup", "run", "cli", "application"})
CONFIG_NAME_RE = re.compile(r"^(\..+|.*config.*|Dockerfile.*|Makefile|Procfile|.*\.ya?ml|.*\.toml|.*\.cfg|.*\.ini|tox\.ini|noxfile\.py)$", re.I)


@dataclass
class Requirement:
    name: str
    file_path: str
    line: int | None
    dev: bool


@dataclass
class PythonAnalysis:
    findings: list[Finding] = field(default_factory=list)
    files_scanned: int = 0
    packages_scanned: int = 0


def normalize(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def import_candidates(distribution: str) -> set[str]:
    norm = normalize(distribution)
    candidates = {norm.replace("-", "_")}
    mapped = IMPORT_NAMES.get(norm)
    if mapped:
        candidates.add(mapped)
    for prefix in ("python-", "py-"):
        if norm.startswith(prefix):
            candidates.add(norm[len(prefix):].replace("-", "_"))
    if norm.startswith("py") and len(norm) > 2:
        candidates.add(norm[2:].replace("-", "_"))
    for suffix in ("-python", "-py", "-binary"):
        if norm.endswith(suffix):
            candidates.add(norm[: -len(suffix)].replace("-", "_"))
    return candidates


def _requirement_name(spec: str) -> str | None:
    spec = spec.split("#", 1)[0].strip()
    if not spec or spec.startswith(("-", "git+", "http:", "https:", ".", "/")):
        return None
    match = REQ_RE.match(spec)
    return match.group(1) if match else None


def _parse_requirements_txt(files: RepoFiles, path: str) -> list[Requirement]:
    text = files.read(path) or ""
    name = path.rsplit("/", 1)[-1].lower()
    dev = any(word in name for word in ("dev", "test", "lint", "docs"))
    found = []
    for number, line in enumerate(text.splitlines(), start=1):
        requirement = _requirement_name(line)
        if requirement:
            found.append(Requirement(requirement, path, number, dev))
    return found


def _line_in(text: str, name: str) -> int | None:
    match = re.search(rf"""["']{re.escape(name)}(?![\w.-])""", text, re.I) or re.search(rf"(?m)^\s*{re.escape(name)}\b", text, re.I)
    return text.count("\n", 0, match.start()) + 1 if match else None


def _parse_pyproject(files: RepoFiles, path: str) -> list[Requirement]:
    text = files.read(path) or ""
    try:
        data = tomllib.loads(text)
    except tomllib.TOMLDecodeError:
        return []
    found: list[Requirement] = []

    def add(specs: object, dev: bool) -> None:
        if not isinstance(specs, list):
            return
        for spec in specs:
            if isinstance(spec, str):
                name = _requirement_name(spec)
                if name:
                    found.append(Requirement(name, path, _line_in(text, name), dev))

    project = data.get("project", {})
    add(project.get("dependencies"), False)
    for group, specs in (project.get("optional-dependencies") or {}).items():
        add(specs, True)
    for group, specs in (data.get("dependency-groups") or {}).items():
        add(specs, True)
    poetry = data.get("tool", {}).get("poetry", {})
    for name in (poetry.get("dependencies") or {}):
        if name.lower() != "python":
            found.append(Requirement(name, path, _line_in(text, name), False))
    for name in (poetry.get("dev-dependencies") or {}):
        found.append(Requirement(name, path, _line_in(text, name), True))
    for group in (poetry.get("group") or {}).values():
        for name in (group.get("dependencies") or {}):
            found.append(Requirement(name, path, _line_in(text, name), True))
    return found


def _top_level_imports(tree: ast.AST) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names.add(node.module.split(".")[0])
    return names


def _referenced_names(tree: ast.AST) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.Attribute):
            names.add(node.attr)
        elif isinstance(node, ast.alias):
            names.add(node.name.split(".")[-1])
            if node.asname:
                names.add(node.asname)
        elif isinstance(node, ast.keyword) and node.arg:
            names.add(node.arg)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value.isidentifier():
            names.add(node.value)
    return names


def _dunder_all(tree: ast.Module) -> set[str]:
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "__all__" for t in node.targets):
            if isinstance(node.value, (ast.List, ast.Tuple)):
                names.update(e.value for e in node.value.elts if isinstance(e, ast.Constant) and isinstance(e.value, str))
    return names


def _config_text(files: RepoFiles, directory: str) -> str:
    prefix = "" if directory == "." else directory + "/"
    chunks = []
    for path in files.paths:
        if not path.startswith(prefix):
            continue
        relative = path[len(prefix):]
        in_ci = relative.startswith((".github/", ".circleci/", ".gitlab/"))
        if ("/" in relative and not in_ci) or path.endswith(".txt"):
            continue
        if CONFIG_NAME_RE.match(relative.rsplit("/", 1)[-1]) or in_ci:
            text = files.read(path)
            if not text or len(text) >= 200_000:
                continue
            if path.endswith("pyproject.toml"):
                # The dependency lists would vouch for themselves, so only read the tool settings and scripts.
                try:
                    data = tomllib.loads(text)
                except tomllib.TOMLDecodeError:
                    continue
                text = repr({"tool": data.get("tool", {}), "scripts": data.get("project", {}).get("scripts", {}),
                             "build": data.get("build-system", {})})
            chunks.append(text)
    return "\n".join(chunks)


CORPUS_SUFFIXES = (".py", ".toml", ".ini", ".cfg", ".yml", ".yaml", ".json")
CORPUS_BYTES = 8_000_000


def _corpus(files: RepoFiles) -> list[tuple[str, str]]:
    """Every Python file and config file except the dependency lists, so a name that appears here is in use somewhere."""
    corpus: list[tuple[str, str]] = []
    budget = CORPUS_BYTES
    for path in files.paths:
        name = path.rsplit("/", 1)[-1]
        if not path.endswith(CORPUS_SUFFIXES) or name == "pyproject.toml" or name.startswith("requirements") or name == "package-lock.json":
            continue
        text = files.read(path)
        if text and budget > 0:
            corpus.append((path, text))
            budget -= len(text)
    return corpus


def _separator_pattern(name: str) -> re.Pattern[str]:
    """Matches a distribution name however it is written: my-pkg, my_pkg or my.pkg."""
    parts = [re.escape(part) for part in re.split(r"[-_.]+", name) if part]
    return re.compile(r"(?<![A-Za-z0-9])" + r"[-_.]".join(parts) + r"(?![A-Za-z0-9])", re.I)


def _is_public_package_module(files: RepoFiles, path: str) -> bool:
    """A module other projects could import: inside a package, with no private (underscore) part in its path."""
    parts = path.split("/")[:-1]
    if not parts or parts[0] in {"examples", "docs", "scripts", "tools", "benchmarks", "tests", "test"}:
        return False
    module = path.rsplit("/", 1)[-1].removesuffix(".py")
    if module.startswith("_") or any(part.startswith("_") for part in parts):
        return False
    return f"{dirname(path)}/__init__.py" in set(files.paths)


def _is_distributed_project(files: RepoFiles) -> bool:
    if any(files.named("setup.py", "setup.cfg")):
        return True
    for manifest in files.named("pyproject.toml"):
        try:
            if "project" in tomllib.loads(files.read(manifest) or ""):
                return True
        except tomllib.TOMLDecodeError:
            continue
    return False


def analyze(files: RepoFiles, include_lint: bool = True) -> PythonAnalysis:
    py_paths = files.with_suffix(".py")
    manifests = files.named("pyproject.toml") + [
        p for p in files.paths if re.match(r"requirements.*\.txt$", p.rsplit("/", 1)[-1], re.I)
    ]
    result = PythonAnalysis(files_scanned=len(py_paths), packages_scanned=len({dirname(m) for m in manifests}))
    if not py_paths:
        return result

    trees: dict[str, ast.Module] = {}
    for path in py_paths:
        text = files.read(path)
        if text is None:
            continue
        try:
            trees[path] = ast.parse(text)
        except (SyntaxError, ValueError):
            continue

    imports = {path: _top_level_imports(tree) for path, tree in trees.items()}
    result.findings.extend(_unused_requirements(files, manifests, trees, imports, _corpus(files)))
    result.findings.extend(_unused_public_names(files, trees))
    if include_lint:
        result.findings.extend(_unused_imports(files, trees))
    return result


def _unused_requirements(
    files: RepoFiles,
    manifests: list[str],
    trees: dict[str, ast.Module],
    imports: dict[str, set[str]],
    corpus_files: list[tuple[str, str]],
) -> list[Finding]:
    findings: list[Finding] = []
    seen: set[tuple[str, str]] = set()
    for manifest in manifests:
        directory = dirname(manifest)
        requirements = (
            _parse_pyproject(files, manifest) if manifest.endswith("pyproject.toml") else _parse_requirements_txt(files, manifest)
        )
        scope = [p for p in trees if is_under(p, directory)]
        used: set[str] = set()
        for path in scope:
            used |= imports[path]
        refs = _config_text(files, directory)
        corpus = [text for path, text in corpus_files if is_under(path, directory)]
        where = "the repo root" if directory == "." else directory
        for requirement in requirements:
            key = (directory, normalize(requirement.name))
            if key in seen:
                continue
            seen.add(key)
            if import_candidates(requirement.name) & used:
                continue
            if re.search(rf"(?<![\w.-]){re.escape(requirement.name)}(?![\w-])", refs, re.I):
                continue
            pattern = _separator_pattern(requirement.name)
            if any(pattern.search(text) for text in corpus):
                continue
            norm = normalize(requirement.name)
            tooling = norm in TOOLING_NAMES or norm.startswith(TOOLING_PREFIXES)
            evidence = (
                f"No Python file under {where} imports '{requirement.name}', and no config file or script mentions it. "
                f"Searched {len(scope)} Python files."
            )
            if tooling:
                evidence += " It looks like a tool or plugin that runs from the command line or a config file, so check before removing it."
            findings.append(
                Finding(
                    UNUSED_DEV_DEPENDENCY if requirement.dev else UNUSED_PACKAGE, directory, requirement.name,
                    requirement.file_path, requirement.line, evidence, UNCERTAIN if tooling else SAFE, "python",
                )
            )
    return findings


def _unused_public_names(files: RepoFiles, trees: dict[str, ast.Module]) -> list[Finding]:
    distributed = _is_distributed_project(files)
    usage: dict[str, set[str]] = {}
    own_references: dict[str, set[str]] = {}
    for path, tree in trees.items():
        own_references[path] = _referenced_names(tree)
        for name in own_references[path]:
            usage.setdefault(name, set()).add(path)

    findings: list[Finding] = []
    total = len(trees)
    for path, tree in trees.items():
        base = path.rsplit("/", 1)[-1]
        if is_test_path(path) or base in {"__init__.py", "__main__.py", "setup.py", "manage.py", "wsgi.py", "asgi.py", "noxfile.py"}:
            continue
        if "migrations" in path.split("/"):
            continue
        exported = _dunder_all(tree)
        for node in tree.body:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            name = node.name
            if name.startswith("_") or name in IGNORED_PUBLIC_NAMES or name in exported or node.decorator_list:
                continue
            if name in own_references[path]:
                continue  # the file calls or refers to it itself, so it isn't dead code
            others = usage.get(name, set()) - {path}
            outside_tests = {o for o in others if not is_test_path(o)}
            if outside_tests:
                continue
            kind = "class" if isinstance(node, ast.ClassDef) else "function"
            searched = f"Searched {total:,} Python files."
            if others:
                evidence = f"{kind.capitalize()} {name} is defined at {path}:{node.lineno} and only test files use it, such as {sorted(others)[0]}. {searched}"
                confidence = UNCERTAIN
            else:
                evidence = f"{kind.capitalize()} {name} is defined at {path}:{node.lineno} and no other file mentions it. {searched}"
                confidence = SAFE
                if isinstance(node, ast.ClassDef) and node.bases:
                    evidence += " It subclasses another class, which a framework can discover without naming it."
                    confidence = UNCERTAIN
                if distributed and _is_public_package_module(files, path):
                    evidence += " It is in a public module of a package other projects can install, so it may be part of its public API."
                    confidence = UNCERTAIN
            findings.append(Finding(UNUSED_EXPORT, dirname(path), name, path, node.lineno, evidence, confidence, "python"))
    return findings


def _unused_imports(files: RepoFiles, trees: dict[str, ast.Module]) -> list[Finding]:
    findings: list[Finding] = []
    for path, tree in trees.items():
        if path.endswith("__init__.py"):
            continue
        exported = _dunder_all(tree)
        used: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                used.add(node.id)
        text = files.read(path) or ""
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                bindings = [(a.asname or a.name.split(".")[0], a.name) for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                if node.module == "__future__":
                    continue
                bindings = [(a.asname or a.name, a.name) for a in node.names if a.name != "*"]
            else:
                continue
            for binding, original in bindings:
                if binding in used or binding in exported or binding == "_":
                    continue
                # A name inside a quoted type hint counts as used.
                if re.search(rf"""['"]{re.escape(binding)}[\w\[\], .|]*['"]""", text):
                    continue
                findings.append(
                    Finding(
                        LINT_ISSUE, dirname(path), f"Unused import '{binding}'", path, node.lineno,
                        f"'{original}' is imported on line {node.lineno} of {path} and is never used in the file.",
                        SAFE, "python", report_only=True,
                    )
                )
    return findings
