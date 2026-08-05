import os
import tempfile
import unittest
from pathlib import Path

from cryptography.fernet import Fernet

from arin_app import db
from arin_app.service import (
    ArinService,
    AuthorizationError,
    ConflictError,
    NotFoundError,
    ValidationError,
)


class ProjectCapabilitiesTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        connection = db.connect(root / "arin.sqlite3")
        db.initialise(connection)
        self.service = ArinService(
            connection,
            asset_root=root / "assets",
            connector_key=Fernet.generate_key(),
        )
        self.connection = connection
        self.owner = self.service.register_user(
            "owner@example.com", "Owner", "a sufficiently long password"
        )
        self.member = self.service.register_user(
            "member@example.com", "Member", "another sufficiently long password"
        )
        self.workspace = self.service.create_workspace(self.owner["id"], "Acme Operations")
        self.service.add_workspace_member(
            self.owner["id"], self.workspace["id"], self.member["id"], "editor"
        )
        self.project = self.service.create_project(
            self.owner["id"],
            self.workspace["id"],
            "Build an operations dashboard",
            "internal",
        )

    def tearDown(self):
        self.connection.close()
        self.tmp.cleanup()

    def test_settings_assets_and_encrypted_connectors_are_project_scoped(self):
        settings = self.service.update_project_settings(
            self.owner["id"],
            self.project["id"],
            {
                "title": "Acme Ops",
                "description": "A private operations workspace",
                "primary_color": "#0f766e",
                "accent_color": "#f59e0b",
                "seo_title": "Acme Operations Dashboard",
                "seo_description": "Track work without spreadsheet chaos.",
            },
        )
        self.assertEqual(settings["title"], "Acme Ops")
        self.assertEqual(settings["primary_color"], "#0f766e")

        asset = self.service.add_asset(
            self.member["id"],
            self.project["id"],
            "brand mark.png",
            "image/png",
            b"\x89PNG\r\n\x1a\nasset-bytes",
        )
        self.assertEqual(asset["original_name"], "brand mark.png")
        self.assertNotEqual(asset["storage_name"], "brand mark.png")
        asset_path = Path(self.tmp.name) / "assets" / asset["storage_name"]
        self.assertTrue(asset_path.is_file())
        self.assertEqual(os.stat(asset_path).st_mode & 0o077, 0)
        self.assertEqual(self.service.list_assets(self.owner["id"], self.project["id"])[0]["id"], asset["id"])

        with self.assertRaises(ValidationError):
            self.service.add_asset(
                self.member["id"], self.project["id"], "shell.sh", "text/x-shellscript", b"echo unsafe"
            )

        connector = self.service.create_connector(
            self.member["id"],
            self.project["id"],
            "webhook",
            "Operations webhook",
            {"url": "https://example.com/hook", "secret": "do-not-leak"},
        )
        self.assertEqual(connector["status"], "active")
        self.assertNotIn("config", connector)
        raw = self.connection.execute(
            "SELECT config_ciphertext FROM connectors WHERE id = ?", (connector["id"],)
        ).fetchone()[0]
        self.assertNotIn("do-not-leak", raw)
        self.assertNotIn("do-not-leak", str(self.service.list_connectors(self.owner["id"], self.project["id"])))
        actions = {
            row["action"]
            for row in self.connection.execute(
                "SELECT action FROM audit_events"
            ).fetchall()
        }
        self.assertTrue(
            {
                "project.settings_updated",
                "project.asset_added",
                "project.connector_created",
            }.issubset(actions)
        )

    def test_owner_invites_member_with_single_use_hashed_token(self):
        invite = self.service.invite_member(
            self.owner["id"], self.workspace["id"], "new@example.com", "viewer"
        )
        self.assertTrue(invite["token"])
        self.assertNotIn("token", self.service.list_invites(self.owner["id"], self.workspace["id"])[0])
        stored = self.connection.execute(
            "SELECT token_hash FROM invites WHERE id = ?", (invite["id"],)
        ).fetchone()[0]
        self.assertNotEqual(stored, invite["token"])

        new_user = self.service.register_user(
            "new@example.com", "New Member", "yet another sufficiently long password"
        )
        accepted = self.service.accept_invite(invite["token"], new_user["id"])
        self.assertEqual(accepted["role"], "viewer")
        self.assertEqual(
            self.service.require_membership(
                new_user["id"], self.workspace["id"], {"viewer"}
            )["role"],
            "viewer",
        )
        with self.assertRaises(ConflictError):
            self.service.accept_invite(invite["token"], new_user["id"])

        with self.assertRaises(AuthorizationError):
            self.service.invite_member(
                self.member["id"], self.workspace["id"], "other@example.com", "viewer"
            )

    def test_agent_history_is_bounded_and_audited(self):
        user_message = self.service.append_agent_message(
            self.member["id"], self.project["id"], "user", "Make the dashboard more concise."
        )
        assistant_message = self.service.append_agent_message(
            self.owner["id"],
            self.project["id"],
            "assistant",
            "I would group the operational metrics into three cards.",
            self.project["current_version_id"],
        )
        messages = self.service.list_agent_messages(self.member["id"], self.project["id"])
        self.assertEqual([row["id"] for row in messages], [user_message["id"], assistant_message["id"]])
        self.assertEqual(messages[1]["version_id"], self.project["current_version_id"])
        self.assertLessEqual(len(messages), 100)

        with self.assertRaises(ValidationError):
            self.service.append_agent_message(
                self.member["id"], self.project["id"], "user", "x" * 33000
            )
        audit_actions = {
            row["action"]
            for row in self.connection.execute(
                "SELECT action FROM audit_events WHERE target_id = ?", (self.project["id"],)
            ).fetchall()
        }
        self.assertIn("agent.message_added", audit_actions)


if __name__ == "__main__":
    unittest.main()
