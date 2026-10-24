# Lopper back end

Python, Flask, and SQLite (development) or Postgres (production). One scanner is shared by three ways to use Lopper:

- the **`lopper` command** in a terminal,
- the **web API**, so someone can paste a repo URL online and get a scan,
- the **VS Code extension** (`../extension`), which runs the `lopper` command in VS Code's terminal.

Lopper reads code and never changes it. It never runs the code it scans.

## Set up

You need Python 3.11 or newer and, nothing else: the API stores its data in a SQLite file.

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate        # macOS and Linux: source .venv/bin/activate
pip install -e ".[dev]"
```

That installs the `lopper` command.

### The database

Data lives in one SQLite file, `backend/lopper.db` (git-ignored), created on first use. To keep it somewhere else, set `DATABASE_PATH`. Nothing has to be started or installed.

For production, set `DATABASE_URL` to a `postgresql://` address (Supabase works) and install the driver with `pip install -e ".[postgres]"`. The code picks the database from that address. `schema.sql` (SQLite) and `schema.postgres.sql` are twins, so change both together. See [DEPLOY.md](../DEPLOY.md).

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
| `PATCH /api/findings/<id>` | Body `{"ticked": true}`. Needs sign-in and a scan you own. Lint issues return `400` |
| `GET /api/auth/me` | `{"user": {...} or null, "sign_in_available": true}` |
| `GET /api/auth/github/login` | Starts signing in: redirects to GitHub |
| `GET /api/auth/github/callback` | GitHub sends the person back here. Redirects to the site |
| `POST /api/auth/logout` | Ends the session |
| `GET /api/repos` | The signed-in person's repos, from GitHub |

```bash
curl -X POST localhost:5000/api/scans -H "Content-Type: application/json" \
     -d '{"repo_url": "https://github.com/pallets/click"}'
curl localhost:5000/api/scans/1
```

A scan's `status` is `running`, `done` or `failed`. Poll `GET /api/scans/<id>` until it isn't `running`. A `failed` scan has an `error` written for the person who pasted the URL.

Only the latest scan is kept for each repo and owner. Scanning again replaces your old scan of that repo and its findings.

### Sign in with GitHub

Signing in lets someone scan repos they can access, including private ones, and keep their tick choices. It is off until you configure it. Without it, everything above still works for public repos.

**Create the GitHub OAuth app** (once):

1. On GitHub, open **Settings → Developer settings → OAuth Apps → New OAuth App**.
2. **Application name:** Lopper (anything you like). **Homepage URL:** `http://localhost:5173`.
3. **Authorization callback URL:** `http://localhost:5173/api/auth/github/callback`. In development the site and the API share one address because Vite forwards `/api` to Flask. In production use `https://your-site/api/auth/github/callback`.
4. Register it, then choose **Generate a new client secret**. Copy the secret straight away, because GitHub shows it once.

**Give the secret to the API.** Copy `.env.example` to `.env` (in `backend/` or the project root, either works) and fill in `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET` and `SECRET_KEY` (the file explains how to make one). To also keep a separate OAuth app for your own machine (callback `http://localhost:5173/api/auth/github/callback`), put its credentials in `CLIENT_ID` and `CLIENT_SECRET`: when both are set they are used instead of the `GITHUB_` pair, and a server that sets only the `GITHUB_` pair uses that one. Then restart `lopper serve`. `.env` is git-ignored. Never commit the secret or paste it into chat.

**Who can see what**

- A scan made while signed in belongs to that person. Only they can read or tick it, and anyone else gets "not found".
- A scan made without signing in is public: anyone can read it, nobody can tick it. Signing in and rescanning gives you your own copy.
- Each person keeps one scan per repo. A public scan and your own scan of the same repo live side by side.

**How it is kept safe**

- The sign-in uses a random one-time `state`, signed and kept in a short-lived `HttpOnly` cookie, so a forged callback is refused.
- The session cookie is a random token (`HttpOnly`, `SameSite=Lax`, and `Secure` when the site is on https). The database stores only its hash.
- GitHub tokens are encrypted at rest with a key made from `SECRET_KEY`. They are passed to `git` through the environment, never the command line, and never appear in a response or an error message.
- Requests that change something are refused if a browser says they came from a different site (`403`).
- If GitHub says a token was revoked, every session for that person ends.

**What Lopper asks GitHub for:** `read:user repo` (change it with `GITHUB_SCOPES`). The `repo` scope is what lets it read private repos, and it is also what opening a pull request will need. GitHub lists the permissions on its consent screen. Lopper only reads today.

Not tested against the real GitHub yet: the handshake is covered with a stand-in for GitHub, and checked on a running server up to the redirect to GitHub.

### Ask about a scan

The results page can offer a panel for questions about a finished scan, such as why an item was flagged or what to check before removing it. Answers come from a model on [OpenRouter](https://openrouter.ai). The chat is off until you set `OPEN_ROUTER_API_KEY` (or OpenRouter's usual `OPENROUTER_API_KEY`) in `.env`, in `backend/` or the project root, and restart; `AI_MODEL` picks the model. `lopper serve` says at startup whether chat is on and which model it uses. Without a key the panel doesn't appear and everything else works as before.

`POST /api/scans/<id>/chat` takes `{"messages": [{"role": "user", "content": "..."}]}`: the whole conversation so far, alternating `user` and `assistant`, ending with a question. It returns `{"reply": "..."}`. Up to 20 messages, 1,000 characters in a question.

- **Who can ask:** anyone who can read the scan. A private scan is only for its owner, and anyone else gets "not found". A public scan can be asked about by anyone.
- **What the model sees:** the server's own copy of the scan (up to 300 findings, with their evidence) and which items are ticked right now. The browser sends only the conversation, so it can't put findings of its own in front of the model. The repo's text goes in the first user message inside `<scan_data>`, with `<` escaped, and the system prompt says to treat it as data.
- **What it can do:** explain. It has no tools, can't tick items, scan or open pull requests, and is told never to say it changed code.
- **Cost and limits:** each question uses your OpenRouter credits. `AI_MODEL` is an OpenRouter model id such as `google/gemini-2.5-flash`, which is also the default (see openrouter.ai/models for prices). One address can send `CHATS_PER_MINUTE` (10) a minute, counted only for questions that get as far as the model. A call times out after 90 seconds, under gunicorn's 120. At most 4 questions can be waiting on the model at once (each holds one of the API's 8 threads), so scans, sign-in and the health check keep theirs; a fifth gets "busy, wait a moment". `CHATS_PER_MINUTE` has to be a whole number of 1 or more, or the server won't start. An answer that runs out of room ends with a note saying it was cut short.
- **What isn't kept:** nothing. Questions and answers aren't stored here. The page keeps the conversation in the browser until you leave it. OpenRouter and the model's provider may keep what they are sent, under their terms and your OpenRouter privacy settings, so don't point chat at repos you wouldn't want them to see.
- **How it is kept safe:** the key stays on the server and is never returned or logged. A failure at OpenRouter becomes fixed text (`chat_unavailable`, `chat_busy` or `chat_failed`) with nothing from its reply in it. If the model declines a question, the person gets a fixed answer.
- **If chat says it isn't working:** the server log says why, with a status and never the key or OpenRouter's message. `401` is a wrong key, `402` means the account is out of credits, and `403` means the key or model isn't allowed. `404` means `AI_MODEL` isn't a model OpenRouter has (the list is at openrouter.ai/models). `429` or `503` is a rate limit or no provider free for that model, and the person is told to wait a moment.

### Settings

Environment variables, all optional (see `.env.example`): `DATABASE_URL` or `DATABASE_PATH`, `PROXY_SECRET`, `CORS_ORIGINS`, `SCAN_WORKERS`, `SCANS_PER_MINUTE`, for chat `OPEN_ROUTER_API_KEY`, `AI_MODEL`, `CHATS_PER_MINUTE`, and for sign-in `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET` (or the local pair `CLIENT_ID`, `CLIENT_SECRET`), `SECRET_KEY`, `FRONTEND_URL`, `GITHUB_SCOPES`. `lopper serve` also reads them from a `.env` file in the current folder, `backend/` or the project root.

### Safety

- Only public `https://github.com/owner/repo` URLs are accepted, so a pasted URL can't point the server at an internal address.
- The repo is shallow-cloned read-only into a temp folder with no prompts, hooks or symlinks, and the folder is deleted afterwards.
- Nothing from the repo is run, imported or installed. Python is parsed with `ast`.
- Limits: 20,000 files, 1 MB per file, 400 MB checkout, 90 seconds to clone, 16 KB request bodies, and 6 scans a minute per address (kept in memory, so it is per process).
- Without signing in, only public repos can be scanned. A private repo fails with a message that points to signing in.

Not built yet: opening the pull request.

## Tests

```bash
python -m pytest
```

The API tests use a real SQLite database: each test gets its own empty file in a temporary folder, so there is nothing to start and nothing to clean up. To run the same tests on Postgres, set `TEST_DATABASE_URL` to an empty Postgres database (for example `postgresql://lopper@localhost:5544/lopper_test`). The tests EMPTY its tables, so never point it at data you care about.

## Layout

| Path | Purpose |
|---|---|
| `lopper/scanner/` | The analysers (`js.py`, `python.py`, `golang.py`) and the models |
| `lopper/repo.py` | Validating a pasted URL and cloning it safely, with or without a GitHub token |
| `lopper/cli.py` | The `lopper` command |
| `lopper/api/` | The Flask app, the schemas (SQLite and Postgres), the scan service, and sign-in (`auth.py`, `auth_routes.py`, `github.py`) |
| `tests/` | Scanner, repo, CLI and API tests |
