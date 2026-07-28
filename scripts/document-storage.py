#!/usr/bin/env python3
"""Migrate and retain encrypted onboarding document objects."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import app


def managed_path(value: str) -> Path:
    root = (app.DATA / "documents").resolve()
    path = Path(value).resolve()
    if path.parent != root:
        raise ValueError(f"Document path is outside managed storage: {path}")
    return path


def migrate(dry_run: bool) -> int:
    migrated = 0
    plaintext_sources: list[Path] = []
    with app.db(immediate=True) as connection:
        rows = connection.execute(
            "SELECT id,storage_path,sha256,metadata FROM uploaded_documents"
        ).fetchall()
        for row in rows:
            metadata = json.loads(row["metadata"])
            if metadata.get("storage_encryption") == "fernet-v1":
                continue
            source = managed_path(row["storage_path"])
            raw = source.read_bytes()
            if hashlib.sha256(raw).hexdigest() != row["sha256"]:
                raise ValueError(f"Plaintext hash mismatch for {row['id']}")
            migrated += 1
            if dry_run:
                continue
            target = app.store_document(row["id"], raw)
            metadata["storage_encryption"] = "fernet-v1"
            connection.execute(
                "UPDATE uploaded_documents SET storage_path=?,metadata=?,updated_at=? WHERE id=?",
                (str(target), json.dumps(metadata), app.utcnow(), row["id"]),
            )
            if source != target:
                plaintext_sources.append(source)
    for source in plaintext_sources:
        source.unlink(missing_ok=True)
    return migrated


def purge(days: int, dry_run: bool) -> int:
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    with app.db(immediate=True) as connection:
        rows = connection.execute(
            """SELECT id,storage_path FROM uploaded_documents
            WHERE status='deleted' AND updated_at < ?""",
            (cutoff,),
        ).fetchall()
        if not dry_run:
            for row in rows:
                managed_path(row["storage_path"]).unlink(missing_ok=True)
                connection.execute(
                    "DELETE FROM uploaded_documents WHERE id=?", (row["id"],)
                )
    return len(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("migrate", "purge"))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--retention-days",
        type=int,
        default=int(os.environ.get("DELETED_DOCUMENT_RETENTION_DAYS", "30")),
    )
    args = parser.parse_args()
    if args.retention_days < 1:
        parser.error("--retention-days must be positive")
    count = (
        migrate(args.dry_run)
        if args.command == "migrate"
        else purge(args.retention_days, args.dry_run)
    )
    mode = "would process" if args.dry_run else "processed"
    print(f"Document storage {args.command}: {mode} {count} record(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
