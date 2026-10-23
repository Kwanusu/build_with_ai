# Lopper back end

Python, Flask and Postgres. One scanner is shared by three ways to use Lopper:

- the **`lopper` command** in a terminal,
- the **web API**, so someone can paste a repo URL online and get a scan,
- the **VS Code extension** (`../extension`), which runs the `lopper` command in VS Code's terminal.

Lopper reads code and never changes it. It never runs the code it scans.

## Set up

You need Python 3.11 or newer and, for the API, Postgres.

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate        # macOS and Linux: source .venv/bin/activate
pip install -e ".[dev]"
```

That installs the `lopper` command.

### A database for development

The quickest way is the throwaway cluster that lives in `backend/.pgdata` and never touches any other Postgres on your machine. It needs the Postgres command line tools on your PATH, or `PG_BIN` set to their folder.

```bash
python scripts/dev_db.py start     # creates it the first time, then starts it on port 5544
python scripts/dev_db.py stop
```

To use your own Postgres instead, create a database and set `DATABASE_URL`, for example `postgresql://user:password@localhost:5432/lopper`.

```bash
lopper db-init                     # creates the tables (safe to run again)
lopper serve                       # API on http://127.0.0.1:5000
```

## The `lopper` command

```bash
lopper scan                                   # scan the current folder
lopper scan path/to/project
lopper scan --url https://github.com/owner/repo
lopper scan --format json --output report.json
lopper scan --no-lint                         # leave out lint issues
lopper scan --strict                          # exit 1 when anything unused is found (for CI)
lopper --version
```

A scan exits with 0 unless you pass `--strict`, so it never blocks a build on its own. Lint issues never count towards `--strict`.

## What it finds

| Language | Unused packages and dev dependencies | Unused exports | Lint issues (report only) |
|---|---|---|---|
| JavaScript and TypeScript | `package.json`, per package in a monorepo | `export` declarations nobody else mentions | Unused imports |
| Python | `requirements*.txt`, `pyproject.toml` | Public functions and classes nobody uses | Unused imports |
| Go | `go.mod` direct requirements | Not checked yet | Not checked yet |

Every finding carries evidence (where it is defined, what was searched) and a confidence:

- **safe**: we found no use anywhere we looked.
- **uncertain**: something means a person should look first. For example a tool that a config file loads by name, a name only tests use, an export reached through a namespace import, or a public module of an installable package.

Safe findings start ticked and uncertain ones start unticked. Lint issues can't be ticked.

### How accurate is it?

The analysis is name-based and conservative, so a missed finding is more likely than a wrong one. It doesn't follow dynamic code, and a name that appears in another file counts as a use. Always read the evidence before removing anything.

We tried it on real public repos while building it. `pallets/click` and `sindresorhus/p-limit` come back with no safe finding that is wrong. Early runs did flag in-use packages as safe (a package loaded by path, Sphinx extensions named in `docs/conf.py`, public API of an installable package), and each of those is now covered by a test.

## The API

All routes are under `/api`. Errors look like `{"error": "...", "code": "..."}` and say whether code was changed.

| Route | What it does |
|---|---|
| `GET /api/health` | `{"status": "ok", "database": true}`, or 503 if the database is down |
| `POST /api/scans` | Body `{"repo_url": "https://github.com/owner/repo"}`. Starts a scan and returns `202` with the scan (status `running`). If that repo is already being scanned it returns `200` with the running one |
| `GET /api/scans/<id>` | The scan with its counts and findings. `?type=unused-export` filters the findings |
| `GET /api/repos/<owner>/<name>/scan` | The latest scan for a repo |
| `PATCH /api/findings/<id>` | Body `{"ticked": true}`. Lint issues return `400` |

```bash
curl -X POST localhost:5000/api/scans -H "Content-Type: application/json" \
     -d '{"repo_url": "https://github.com/pallets/click"}'
curl localhost:5000/api/scans/1
```

A scan's `status` is `running`, `done` or `failed`. Poll `GET /api/scans/<id>` until it isn't `running`. A `failed` scan has an `error` written for the person who pasted the URL.

Only the latest scan is kept per repo. Scanning again replaces the old scan and its findings.

### Settings

Environment variables, all optional (see `.env.example`): `DATABASE_URL`, `CORS_ORIGINS`, `SCAN_WORKERS`, `SCANS_PER_MINUTE`.

### Safety

- Only public `https://github.com/owner/repo` URLs are accepted, so a pasted URL can't point the server at an internal address.
- The repo is shallow-cloned read-only into a temp folder with no prompts, hooks or symlinks, and the folder is deleted afterwards.
- Nothing from the repo is run, imported or installed. Python is parsed with `ast`.
- Limits: 20,000 files, 1 MB per file, 400 MB checkout, 90 seconds to clone, 16 KB request bodies, and 6 scans a minute per address (kept in memory, so it is per process).
- Private repos aren't supported yet. A private repo fails with a clear message.

Not built yet: signing in with GitHub and opening the pull request.

## Tests

```bash
python -m pytest
```

The API tests use a real Postgres at `TEST_DATABASE_URL` (default `postgresql://lopper@localhost:5544/lopper_test`, which `dev_db.py start` creates). They are skipped, with a reason, if it isn't reachable. They empty the tables in that database, so never point it at data you care about.

## Layout

| Path | Purpose |
|---|---|
| `lopper/scanner/` | The analysers (`js.py`, `python.py`, `golang.py`) and the models |
| `lopper/repo.py` | Validating a pasted URL and cloning it safely |
| `lopper/cli.py` | The `lopper` command |
| `lopper/api/` | The Flask app, the Postgres schema and the scan service |
| `scripts/dev_db.py` | The throwaway development database |
| `tests/` | Scanner, repo, CLI and API tests |
