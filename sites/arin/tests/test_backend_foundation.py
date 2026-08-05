import sqlite3
import tempfile
import unittest
from pathlib import Path

from arin_app import db, security


class BackendFoundationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.database_path = Path(self.tmp.name) / "arin.sqlite3"
        self.connection = db.connect(self.database_path)
        db.initialise(self.connection)

    def tearDown(self):
        self.connection.close()
        self.tmp.cleanup()

    def test_database_enables_wal_foreign_keys_and_required_tables(self):
        self.assertEqual(self.connection.execute("PRAGMA foreign_keys").fetchone()[0], 1)
        self.assertEqual(self.connection.execute("PRAGMA journal_mode").fetchone()[0], "wal")
        names = {
            row[0]
            for row in self.connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        self.assertTrue(
            {
                "users",
                "sessions",
                "workspaces",
                "workspace_members",
                "projects",
                "project_versions",
                "project_files",
                "project_assets",
                "connectors",
                "invites",
                "agent_messages",
                "deployments",
                "audit_events",
            }.issubset(names)
        )

    def test_transaction_rolls_back_all_writes_after_exception(self):
        with self.assertRaisesRegex(RuntimeError, "rollback sentinel"):
            with db.transaction(self.connection):
                self.connection.execute(
                    "INSERT INTO users (id, email, name, password_hash, password_salt, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        "usr_test",
                        "test@example.com",
                        "Test",
                        "hash",
                        "salt",
                        "2026-08-02T00:00:00+00:00",
                        "2026-08-02T00:00:00+00:00",
                    ),
                )
                raise RuntimeError("rollback sentinel")

        self.assertIsNone(
            self.connection.execute(
                "SELECT id FROM users WHERE id = ?", ("usr_test",)
            ).fetchone()
        )

    def test_password_hash_is_salted_and_verifies_only_original_password(self):
        encoded, salt = security.hash_password("correct horse battery staple")
        self.assertNotEqual(encoded, "correct horse battery staple")
        self.assertTrue(
            security.verify_password("correct horse battery staple", encoded, salt)
        )
        self.assertFalse(security.verify_password("wrong password", encoded, salt))

        other_encoded, other_salt = security.hash_password("correct horse battery staple")
        self.assertNotEqual((encoded, salt), (other_encoded, other_salt))

    def test_tokens_are_random_and_only_the_hash_is_stable(self):
        token = security.new_token()
        self.assertGreaterEqual(len(token), 32)
        self.assertNotEqual(token, security.hash_token(token))
        self.assertEqual(security.hash_token(token), security.hash_token(token))
        self.assertNotEqual(token, security.new_token())

    def test_password_validator_rejects_short_or_empty_values(self):
        for value in ("", "short", "\n" * 12):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    security.validate_password(value)
        security.validate_password("a sufficiently long password")


if __name__ == "__main__":
    unittest.main()
