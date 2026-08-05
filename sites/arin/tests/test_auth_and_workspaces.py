import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from arin_app import db
from arin_app.service import (
    ArinService,
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    SessionError,
)


class AuthAndWorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        connection = db.connect(Path(self.tmp.name) / "arin.sqlite3")
        db.initialise(connection)
        self.service = ArinService(connection)
        self.connection = connection

    def tearDown(self):
        self.connection.close()
        self.tmp.cleanup()

    def test_registration_normalizes_email_and_rejects_duplicate_identity(self):
        user = self.service.register_user("  Owner@Example.COM ", "Owner", "a sufficiently long password")
        self.assertEqual(user["email"], "owner@example.com")
        with self.assertRaises(ConflictError):
            self.service.register_user("owner@example.com", "Other", "another long password")

    def test_login_returns_opaque_session_and_csrf_values(self):
        user = self.service.register_user("owner@example.com", "Owner", "a sufficiently long password")
        session = self.service.login_user("OWNER@example.com", "a sufficiently long password")

        self.assertEqual(session["user"]["id"], user["id"])
        self.assertGreaterEqual(len(session["session_token"]), 32)
        self.assertGreaterEqual(len(session["csrf_token"]), 32)
        self.assertIsNotNone(
            self.service.authenticate_session(
                session["session_token"], session["csrf_token"]
            )
        )
        with self.assertRaises(AuthenticationError):
            self.service.login_user("owner@example.com", "wrong password")

    def test_expired_session_and_csrf_mismatch_are_rejected(self):
        self.service.register_user("owner@example.com", "Owner", "a sufficiently long password")
        session = self.service.login_user("owner@example.com", "a sufficiently long password")

        with self.assertRaises(SessionError):
            self.service.authenticate_session(session["session_token"], "wrong-csrf")

        self.connection.execute(
            "UPDATE sessions SET expires_at = ? WHERE token_hash = ?",
            (
                (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat(),
                self.service.hash_session_token(session["session_token"]),
            ),
        )
        with self.assertRaises(SessionError):
            self.service.authenticate_session(
                session["session_token"], session["csrf_token"]
            )

    def test_workspace_owner_editor_and_viewer_permissions_are_enforced(self):
        owner = self.service.register_user("owner@example.com", "Owner", "a sufficiently long password")
        editor = self.service.register_user("editor@example.com", "Editor", "another long password")
        viewer = self.service.register_user("viewer@example.com", "Viewer", "yet another password")
        workspace = self.service.create_workspace(owner["id"], "Acme Operations")
        self.service.add_workspace_member(owner["id"], workspace["id"], editor["id"], "editor")
        self.service.add_workspace_member(owner["id"], workspace["id"], viewer["id"], "viewer")

        self.assertEqual(
            self.service.require_membership(owner["id"], workspace["id"], {"owner"})["role"],
            "owner",
        )
        self.assertEqual(
            self.service.require_membership(editor["id"], workspace["id"], {"owner", "editor"})["role"],
            "editor",
        )
        with self.assertRaises(AuthorizationError):
            self.service.require_membership(viewer["id"], workspace["id"], {"owner", "editor"})
        with self.assertRaises(AuthorizationError):
            self.service.add_workspace_member(viewer["id"], workspace["id"], editor["id"], "viewer")

    def test_logout_revokes_session(self):
        self.service.register_user("owner@example.com", "Owner", "a sufficiently long password")
        session = self.service.login_user("owner@example.com", "a sufficiently long password")
        self.service.logout(session["session_token"])
        with self.assertRaises(SessionError):
            self.service.authenticate_session(
                session["session_token"], session["csrf_token"]
            )


if __name__ == "__main__":
    unittest.main()
