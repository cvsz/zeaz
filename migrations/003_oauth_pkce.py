"""Add encrypted PKCE verifier storage and invalidate pre-PKCE OAuth states."""
from __future__ import annotations

import sqlite3


def upgrade(connection: sqlite3.Connection) -> None:
    columns = {
        row[1] for row in connection.execute("PRAGMA table_info(oauth_states)")
    }
    if "verifier_cipher" not in columns:
        connection.execute(
            "ALTER TABLE oauth_states ADD COLUMN verifier_cipher TEXT NOT NULL DEFAULT ''"
        )
    connection.execute("DELETE FROM oauth_states")
