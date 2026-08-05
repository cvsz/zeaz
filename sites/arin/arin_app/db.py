"""SQLite persistence primitives for the Arin service."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT NOT NULL COLLATE NOCASE UNIQUE,
    name TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    password_salt TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
    token_hash TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    csrf_token_hash TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    created_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS sessions_user_idx ON sessions(user_id);

CREATE TABLE IF NOT EXISTS workspaces (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    owner_id TEXT NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS workspace_members (
    workspace_id TEXT NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('owner', 'editor', 'viewer')),
    created_at TEXT NOT NULL,
    PRIMARY KEY (workspace_id, user_id)
);
CREATE INDEX IF NOT EXISTS workspace_members_user_idx ON workspace_members(user_id);

CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    slug TEXT NOT NULL,
    prompt TEXT NOT NULL,
    category TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('draft', 'published', 'archived')),
    current_version_id TEXT,
    settings_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE (workspace_id, slug)
);
CREATE INDEX IF NOT EXISTS projects_workspace_idx ON projects(workspace_id);

CREATE TABLE IF NOT EXISTS project_versions (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    source TEXT NOT NULL,
    created_by TEXT NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    created_at TEXT NOT NULL,
    UNIQUE (project_id, version_number)
);

CREATE TABLE IF NOT EXISTS project_files (
    version_id TEXT NOT NULL REFERENCES project_versions(id) ON DELETE CASCADE,
    path TEXT NOT NULL,
    mime_type TEXT NOT NULL,
    content TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    PRIMARY KEY (version_id, path)
);

CREATE TABLE IF NOT EXISTS project_assets (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    original_name TEXT NOT NULL,
    storage_name TEXT NOT NULL UNIQUE,
    mime_type TEXT NOT NULL,
    size_bytes INTEGER NOT NULL CHECK (size_bytes >= 0),
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS connectors (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    kind TEXT NOT NULL,
    label TEXT NOT NULL,
    config_ciphertext TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('active', 'disabled', 'error')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS invites (
    id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    email TEXT NOT NULL COLLATE NOCASE,
    role TEXT NOT NULL CHECK (role IN ('editor', 'viewer')),
    token_hash TEXT NOT NULL UNIQUE,
    expires_at TEXT NOT NULL,
    accepted_at TEXT,
    invited_by TEXT NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS agent_messages (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    version_id TEXT REFERENCES project_versions(id) ON DELETE SET NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS agent_messages_project_idx ON agent_messages(project_id, created_at);

CREATE TABLE IF NOT EXISTS deployments (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    slug TEXT NOT NULL UNIQUE,
    version_id TEXT NOT NULL REFERENCES project_versions(id) ON DELETE RESTRICT,
    status TEXT NOT NULL CHECK (status IN ('published', 'unpublished')),
    created_at TEXT NOT NULL,
    published_at TEXT
);
CREATE INDEX IF NOT EXISTS deployments_project_idx ON deployments(project_id);

CREATE TABLE IF NOT EXISTS audit_events (
    id TEXT PRIMARY KEY,
    actor_id TEXT REFERENCES users(id) ON DELETE SET NULL,
    action TEXT NOT NULL,
    target_type TEXT NOT NULL,
    target_id TEXT NOT NULL,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS audit_events_target_idx ON audit_events(target_type, target_id, created_at);
"""


def connect(path: Path) -> sqlite3.Connection:
    """Open a private SQLite connection configured for Arin transactions."""

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        path.parent.chmod(0o700)
    except PermissionError:
        pass
    # The HTTP service shares one connection behind its service request lock;
    # allowing worker threads to use that connection is safe because the lock
    # serializes each request's transaction boundary.
    connection = sqlite3.connect(
        path, timeout=10, isolation_level=None, check_same_thread=False
    )
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA journal_mode = WAL")
    connection.execute("PRAGMA synchronous = NORMAL")
    try:
        path.chmod(0o600)
    except FileNotFoundError:
        pass
    return connection


def initialise(connection: sqlite3.Connection) -> None:
    """Create the additive Arin schema and indexes."""

    # sqlite3.executescript() manages its own DDL transaction and implicitly
    # commits any active transaction before running the script. Keep it outside
    # the application write-transaction helper so schema bootstrap cannot try
    # to commit a transaction that SQLite has already closed.
    connection.executescript(SCHEMA)


@contextmanager
def transaction(connection: sqlite3.Connection) -> Iterator[sqlite3.Connection]:
    """Run a write transaction that rolls back as one unit on any exception."""

    connection.execute("BEGIN IMMEDIATE")
    try:
        yield connection
    except BaseException:
        connection.execute("ROLLBACK")
        raise
    else:
        connection.execute("COMMIT")
