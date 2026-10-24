"""The `lopper` command. VS Code runs this same command in its terminal."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .dotenv import load_dotenv
from .repo import RepoError, checkout, parse_repo_url
from .scanner import ScanLimitError, ScanResult, scan_path

LABELS = {
    "unused-package": ("unused package", "unused packages"),
    "unused-dev-dependency": ("unused dev dependency", "unused dev dependencies"),
    "unused-export": ("unused export", "unused exports"),
    "lint-issue": ("lint issue", "lint issues"),
}


def _plural(count: int, kind: str) -> str:
    singular, plural = LABELS[kind]
    return f"{count:,} {singular if count == 1 else plural}"


def format_text(result: ScanResult, source: str) -> str:
    counts = result.counts()
    lines = [f"Lopper scanned {source}", ""]
    lines.append(
        f"Searched {result.files_scanned:,} files across {result.packages_scanned} "
        f"package{'s' if result.packages_scanned != 1 else ''}"
        + (f" ({', '.join(result.languages)})." if result.languages else ".")
    )
    if not result.findings:
        lines += ["", "We found no unused packages, exports or lint issues. Nothing was changed."]
        return "\n".join(lines)

    total = sum(counts[k] for k in counts if k != "lint-issue")
    lines += ["", f"Found {total:,} unused item{'s' if total != 1 else ''}: " + ", ".join(
        _plural(counts[k], k) for k in LABELS if k != "lint-issue" and counts[k]
    ) + "." if total else "Found no unused packages or exports."]
    if counts["lint-issue"]:
        lines.append(f"Also found {_plural(counts['lint-issue'], 'lint-issue')}. Lint issues are report only.")

    for kind in LABELS:
        group = [f for f in result.findings if f.type == kind]
        if not group:
            continue
        title = LABELS[kind][1].capitalize() + (" (report only)" if kind == "lint-issue" else "")
        lines += ["", f"{title}", "-" * len(title)]
        for finding in group:
            location = finding.file_path + (f":{finding.line}" if finding.line else "")
            mark = "needs a closer look" if finding.confidence == "uncertain" else "no use found"
            lines.append(f"  {finding.item}  [{mark}]")
            lines.append(f"    {location}")
            lines.append(f"    {finding.evidence}")
    lines += ["", "Nothing was changed. Lopper reads your code and never removes anything on its own."]
    return "\n".join(lines)


def _scan(args: argparse.Namespace) -> int:
    include_lint = not args.no_lint
    try:
        if args.url:
            ref = parse_repo_url(args.url)
            with checkout(ref) as folder:
                result = scan_path(folder, include_lint=include_lint)
            source = ref.url
        else:
            folder = Path(args.path).resolve()
            result = scan_path(folder, include_lint=include_lint)
            source = str(folder)
    except (RepoError, ScanLimitError, NotADirectoryError) as error:
        print(f"We couldn't finish scanning. Your code hasn't been changed. {error}", file=sys.stderr)
        return 2

    if args.format == "json":
        output = json.dumps({"source": source, **result.to_dict()}, indent=2)
    else:
        output = format_text(result, source)
    if args.output:
        Path(args.output).write_text(output + "\n", encoding="utf-8")
        print(f"Report written to {args.output}")
    else:
        print(output)
    # Scans report and people remove. Exit non-zero only when asked, so a scan never blocks a build by default.
    if args.strict and any(not f.report_only for f in result.findings):
        return 1
    return 0


def sign_in_banner(config) -> str:
    """What to tell the person starting the server about GitHub sign-in. A Client ID is public, so it is safe to print."""
    if not config.auth_enabled:
        return "GitHub sign-in is off (it needs a Client ID, a Client secret and a SECRET_KEY in .env)."
    return (
        f"GitHub sign-in is on, using the {config.github_app} OAuth app (Client ID {config.github_client_id}).\n"
        f"That app's callback URL must be exactly {config.frontend_url}/api/auth/github/callback"
    )


def chat_banner(config) -> str:
    """What to tell the person starting the server about the chat panel. The model name is public, the key never printed."""
    if not config.chat_api_key:
        return "Chat is off (it needs OPEN_ROUTER_API_KEY in .env)."
    return f"Chat is on, using the model {config.chat_model} through OpenRouter. Each question uses your OpenRouter credits."


def _serve(args: argparse.Namespace) -> int:
    from .api import create_app

    load_dotenv()  # settings and the GitHub app's secret can live in backend/.env

    app = create_app()
    config = app.extensions["lopper_config"]
    print(sign_in_banner(config), flush=True)
    print(chat_banner(config), flush=True)
    app.run(host=args.host, port=args.port, debug=args.debug)
    return 0


def _db_init(_args: argparse.Namespace) -> int:
    from .api import create_app
    from .api.db import init_db

    load_dotenv()

    app = create_app(init=False)
    with app.app_context():
        init_db()
    print("Database is ready.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lopper", description="Find unused packages, exports and dev dependencies, with the evidence. Reads code, never changes it."
    )
    parser.add_argument("--version", action="version", version=f"lopper {__version__}")
    commands = parser.add_subparsers(dest="command", required=True)

    scan = commands.add_parser("scan", help="scan a folder or a public GitHub repo")
    scan.add_argument("path", nargs="?", default=".", help="folder to scan (default: the current folder)")
    scan.add_argument("--url", help="scan a public GitHub repo instead, e.g. https://github.com/owner/repo")
    scan.add_argument("--format", choices=("text", "json"), default="text")
    scan.add_argument("--output", "-o", help="write the report to a file instead of printing it")
    scan.add_argument("--no-lint", action="store_true", help="skip lint issues (they are report only anyway)")
    scan.add_argument("--strict", action="store_true", help="exit with 1 when anything unused is found (for CI)")
    scan.set_defaults(handler=_scan)

    serve = commands.add_parser("serve", help="run the API server")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=5000)
    serve.add_argument("--debug", action="store_true")
    serve.set_defaults(handler=_serve)

    init = commands.add_parser("db-init", help="create the database tables")
    init.set_defaults(handler=_db_init)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.handler(args)


if __name__ == "__main__":
    sys.exit(main())
