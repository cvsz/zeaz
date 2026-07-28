"""Checksummed, transactional SQLite migration runner."""
from __future__ import annotations

import hashlib
import importlib.util
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

MIGRATIONS = Path(__file__).resolve().parent
MIGRATION_NAME = re.compile(r"^(\d{3})_([a-z0-9_]+)\.(sql|py)$")


class MigrationError(RuntimeError):
    """Raised when migration history or execution is unsafe."""


def _discover(directory: Path) -> list[tuple[int, str, Path, str]]:
    migrations = []
    seen: set[int] = set()
    for path in sorted(directory.iterdir()):
        match = MIGRATION_NAME.match(path.name)
        if not match:
            continue
        version = int(match.group(1))
        if version in seen:
            raise MigrationError(f"Duplicate migration version {version:03d}")
        seen.add(version)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        migrations.append((version, path.name, path, digest))
    return migrations


def _load_python(path: Path):
    spec = importlib.util.spec_from_file_location(f"zeaz_migration_{path.stem}", path)
    if spec is None or spec.loader is None:
        raise MigrationError(f"Cannot load migration {path.name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    upgrade = getattr(module, "upgrade", None)
    if not callable(upgrade):
        raise MigrationError(f"Migration {path.name} has no upgrade(connection)")
    return upgrade


def _sql_statements(script: str) -> list[str]:
    statements = []
    pending = ""
    for line in script.splitlines(keepends=True):
        pending += line
        if sqlite3.complete_statement(pending):
            if pending.strip():
                statements.append(pending)
            pending = ""
    if pending.strip():
        raise MigrationError("SQL migration ends with an incomplete statement")
    return statements


def apply_migrations(
    connection: sqlite3.Connection, migrations_dir: Path = MIGRATIONS
) -> list[int]:
    connection.execute("PRAGMA foreign_keys=ON")
    connection.execute("PRAGMA busy_timeout=10000")
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute(
        """CREATE TABLE IF NOT EXISTS schema_migrations (
        version INTEGER PRIMARY KEY,
        name TEXT NOT NULL UNIQUE,
        sha256 TEXT NOT NULL,
        applied_at TEXT NOT NULL
        )"""
    )
    discovered = _discover(migrations_dir)
    known = {version: (name, digest) for version, name, _, digest in discovered}
    applied = {
        row[0]: (row[1], row[2])
        for row in connection.execute(
            "SELECT version,name,sha256 FROM schema_migrations ORDER BY version"
        )
    }
    unknown = sorted(set(applied) - set(known))
    if unknown:
        raise MigrationError(f"Database contains unknown migrations: {unknown}")
    for version, (name, digest) in applied.items():
        if known[version] != (name, digest):
            raise MigrationError(f"Migration {version:03d} checksum or name changed")

    completed = []
    for version, name, path, digest in discovered:
        if version in applied:
            continue
        applied_at = datetime.now(timezone.utc).isoformat()
        if path.suffix == ".sql":
            try:
                connection.execute("BEGIN IMMEDIATE")
                concurrent = connection.execute(
                    "SELECT name,sha256 FROM schema_migrations WHERE version=?",
                    (version,),
                ).fetchone()
                if concurrent:
                    if tuple(concurrent) != (name, digest):
                        raise MigrationError(
                            f"Migration {version:03d} changed during startup"
                        )
                    connection.commit()
                    continue
                for statement in _sql_statements(path.read_text(encoding="utf-8")):
                    connection.execute(statement)
                connection.execute(
                    "INSERT INTO schema_migrations VALUES (?,?,?,?)",
                    (version, name, digest, applied_at),
                )
                connection.commit()
            except Exception:
                connection.rollback()
                raise
        else:
            try:
                connection.execute("BEGIN IMMEDIATE")
                concurrent = connection.execute(
                    "SELECT name,sha256 FROM schema_migrations WHERE version=?",
                    (version,),
                ).fetchone()
                if concurrent:
                    if tuple(concurrent) != (name, digest):
                        raise MigrationError(
                            f"Migration {version:03d} changed during startup"
                        )
                    connection.commit()
                    continue
                _load_python(path)(connection)
                connection.execute(
                    "INSERT INTO schema_migrations VALUES (?,?,?,?)",
                    (version, name, digest, applied_at),
                )
                connection.commit()
            except Exception:
                connection.rollback()
                raise
        completed.append(version)
    return completed
