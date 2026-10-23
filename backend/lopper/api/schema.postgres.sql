-- Lopper schema (Postgres, for example Supabase). Safe to run more than once. schema.sql is the SQLite twin: keep them in step.
--
-- A scan made while signed in belongs to that user and is private to them. A scan made without
-- signing in is public and read-only. Only the latest scan is kept for each repo and owner, and a
-- scan's findings are replaced with it. `languages` is a JSON list kept as text, like in SQLite.
--
-- The API is the only thing that should read these tables, and it uses a server-side connection.
-- Row level security is switched on with no policies, so Supabase's public REST API can't read them.

CREATE TABLE IF NOT EXISTS users (
    id                      BIGSERIAL PRIMARY KEY,
    github_id               BIGINT NOT NULL UNIQUE,
    login                   TEXT NOT NULL,
    avatar_url              TEXT,
    access_token_encrypted  TEXT NOT NULL,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_signed_in_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- The cookie holds a random token. Only its hash is stored, so a copy of this table can't be used to sign in.
CREATE TABLE IF NOT EXISTS sessions (
    token_hash  TEXT PRIMARY KEY,
    user_id     BIGINT NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at  TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS sessions_user_id_idx ON sessions (user_id);

CREATE TABLE IF NOT EXISTS repos (
    id          BIGSERIAL PRIMARY KEY,
    url         TEXT NOT NULL UNIQUE,
    owner       TEXT NOT NULL,
    name        TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS scans (
    id                BIGSERIAL PRIMARY KEY,
    repo_id           BIGINT NOT NULL REFERENCES repos (id) ON DELETE CASCADE,
    user_id           BIGINT REFERENCES users (id) ON DELETE CASCADE,
    status            TEXT NOT NULL CHECK (status IN ('running', 'done', 'failed')),
    started_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at       TIMESTAMPTZ,
    error             TEXT,
    files_scanned     INTEGER NOT NULL DEFAULT 0,
    packages_scanned  INTEGER NOT NULL DEFAULT 0,
    languages         TEXT NOT NULL DEFAULT '[]'
);

CREATE UNIQUE INDEX IF NOT EXISTS scans_one_public_per_repo ON scans (repo_id) WHERE user_id IS NULL;
CREATE UNIQUE INDEX IF NOT EXISTS scans_one_per_repo_and_user ON scans (repo_id, user_id) WHERE user_id IS NOT NULL;

CREATE TABLE IF NOT EXISTS findings (
    id           BIGSERIAL PRIMARY KEY,
    scan_id      BIGINT NOT NULL REFERENCES scans (id) ON DELETE CASCADE,
    type         TEXT NOT NULL CHECK (type IN ('unused-package', 'unused-export', 'unused-dev-dependency', 'lint-issue')),
    package      TEXT NOT NULL,
    item         TEXT NOT NULL,
    file_path    TEXT NOT NULL,
    line         INTEGER,
    evidence     TEXT NOT NULL,
    confidence   TEXT NOT NULL CHECK (confidence IN ('safe', 'uncertain')),
    language     TEXT NOT NULL,
    report_only  BOOLEAN NOT NULL DEFAULT FALSE,
    ticked       BOOLEAN NOT NULL DEFAULT FALSE,
    CHECK (NOT (report_only AND ticked))
);

CREATE INDEX IF NOT EXISTS findings_scan_id_idx ON findings (scan_id, type);

ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE repos ENABLE ROW LEVEL SECURITY;
ALTER TABLE scans ENABLE ROW LEVEL SECURITY;
ALTER TABLE findings ENABLE ROW LEVEL SECURITY;
