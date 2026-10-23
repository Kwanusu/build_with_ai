-- Lopper schema (SQLite). Safe to run more than once.
--
-- A scan made while signed in belongs to that user and is private to them. A scan made without
-- signing in is public and read-only. Only the latest scan is kept for each repo and owner, and a
-- scan's findings are replaced with it.
--
-- Times are UTC text like 2026-10-23T19:46:33.123Z. Booleans are 0 or 1. `languages` is a JSON list.

CREATE TABLE IF NOT EXISTS users (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    github_id               INTEGER NOT NULL UNIQUE,
    login                   TEXT NOT NULL,
    avatar_url              TEXT,
    access_token_encrypted  TEXT NOT NULL,
    created_at              TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    last_signed_in_at       TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

-- The cookie holds a random token. Only its hash is stored, so a copy of this table can't be used to sign in.
CREATE TABLE IF NOT EXISTS sessions (
    token_hash  TEXT PRIMARY KEY,
    user_id     INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    expires_at  TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS sessions_user_id_idx ON sessions (user_id);

CREATE TABLE IF NOT EXISTS repos (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    url         TEXT NOT NULL UNIQUE,
    owner       TEXT NOT NULL,
    name        TEXT NOT NULL,
    created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE TABLE IF NOT EXISTS scans (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    repo_id           INTEGER NOT NULL REFERENCES repos (id) ON DELETE CASCADE,
    user_id           INTEGER REFERENCES users (id) ON DELETE CASCADE,
    status            TEXT NOT NULL CHECK (status IN ('running', 'done', 'failed')),
    started_at        TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    finished_at       TEXT,
    error             TEXT,
    files_scanned     INTEGER NOT NULL DEFAULT 0,
    packages_scanned  INTEGER NOT NULL DEFAULT 0,
    languages         TEXT NOT NULL DEFAULT '[]'
);

CREATE UNIQUE INDEX IF NOT EXISTS scans_one_public_per_repo ON scans (repo_id) WHERE user_id IS NULL;
CREATE UNIQUE INDEX IF NOT EXISTS scans_one_per_repo_and_user ON scans (repo_id, user_id) WHERE user_id IS NOT NULL;

CREATE TABLE IF NOT EXISTS findings (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    scan_id      INTEGER NOT NULL REFERENCES scans (id) ON DELETE CASCADE,
    type         TEXT NOT NULL CHECK (type IN ('unused-package', 'unused-export', 'unused-dev-dependency', 'lint-issue')),
    package      TEXT NOT NULL,
    item         TEXT NOT NULL,
    file_path    TEXT NOT NULL,
    line         INTEGER,
    evidence     TEXT NOT NULL,
    confidence   TEXT NOT NULL CHECK (confidence IN ('safe', 'uncertain')),
    language     TEXT NOT NULL,
    report_only  INTEGER NOT NULL DEFAULT 0 CHECK (report_only IN (0, 1)),
    ticked       INTEGER NOT NULL DEFAULT 0 CHECK (ticked IN (0, 1)),
    CHECK (NOT (report_only AND ticked))
);

CREATE INDEX IF NOT EXISTS findings_scan_id_idx ON findings (scan_id, type);
