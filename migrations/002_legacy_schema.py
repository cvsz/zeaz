"""Repair schemas created by pre-ledger application versions."""
from __future__ import annotations

import sqlite3


def upgrade(connection: sqlite3.Connection) -> None:
    payment = connection.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='payment_attempts'"
    ).fetchone()
    if payment and "'refunded'" not in payment[0]:
        connection.execute("DROP INDEX IF EXISTS idx_payment_attempts_order")
        connection.execute("DROP INDEX IF EXISTS idx_payment_attempts_provider_order")
        connection.execute("ALTER TABLE payment_attempts RENAME TO payment_attempts_legacy")
        connection.execute(
            """CREATE TABLE payment_attempts (
            id TEXT PRIMARY KEY,
            order_id TEXT NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
            provider TEXT NOT NULL,
            provider_reference TEXT NOT NULL UNIQUE,
            provider_order_id TEXT UNIQUE,
            amount INTEGER NOT NULL CHECK(amount >= 0),
            status TEXT NOT NULL CHECK(status IN
              ('created','pending','paid','failed','expired','cancelled','refunded')),
            qr_image TEXT NOT NULL DEFAULT '',
            qr_type TEXT NOT NULL DEFAULT '',
            expires_at TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            confirmed_at TEXT NOT NULL DEFAULT '',
            provider_response TEXT NOT NULL DEFAULT '{}'
            )"""
        )
        connection.execute(
            """INSERT INTO payment_attempts(
            id,order_id,provider,provider_reference,provider_order_id,amount,status,
            qr_image,qr_type,expires_at,created_at,updated_at,confirmed_at,provider_response
            )
            SELECT id,order_id,provider,provider_reference,provider_order_id,amount,status,
            qr_image,qr_type,expires_at,created_at,updated_at,confirmed_at,provider_response
            FROM payment_attempts_legacy"""
        )
        connection.execute("DROP TABLE payment_attempts_legacy")
        connection.execute(
            "CREATE INDEX idx_payment_attempts_order ON payment_attempts(order_id,created_at DESC)"
        )
        connection.execute(
            "CREATE INDEX idx_payment_attempts_provider_order ON payment_attempts(provider,provider_order_id)"
        )
    deliveries = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='deliveries'"
    ).fetchone()
    if deliveries:
        columns = {
            row[1] for row in connection.execute("PRAGMA table_info(deliveries)")
        }
        if "distance_km" not in columns:
            connection.execute(
                "ALTER TABLE deliveries ADD COLUMN distance_km REAL NOT NULL DEFAULT 0"
            )
