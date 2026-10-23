-- Lopper schema. Safe to run more than once.
-- Only the latest scan is kept per repo, and each scan's findings are replaced with it.

CREATE TABLE IF NOT EXISTS repos (
    id          BIGSERIAL PRIMARY KEY,
    url         TEXT NOT NULL UNIQUE,
    owner       TEXT NOT NULL,
    name        TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS scans (
    id                BIGSERIAL PRIMARY KEY,
    repo_id           BIGINT NOT NULL UNIQUE REFERENCES repos (id) ON DELETE CASCADE,
    status            TEXT NOT NULL CHECK (status IN ('running', 'done', 'failed')),
    started_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at       TIMESTAMPTZ,
    error             TEXT,
    files_scanned     INTEGER NOT NULL DEFAULT 0,
    packages_scanned  INTEGER NOT NULL DEFAULT 0,
    languages         TEXT[] NOT NULL DEFAULT '{}'
);

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
