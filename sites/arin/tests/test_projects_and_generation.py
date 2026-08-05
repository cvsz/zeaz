import tempfile
import unittest
from pathlib import Path

from arin_app import db
from arin_app.generator import generate_project
from arin_app.service import ArinService, NotFoundError, ValidationError


class ProjectGenerationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        connection = db.connect(Path(self.tmp.name) / "arin.sqlite3")
        db.initialise(connection)
        self.service = ArinService(connection)
        self.connection = connection
        self.user = self.service.register_user(
            "owner@example.com", "Owner", "a sufficiently long password"
        )
        self.workspace = self.service.create_workspace(self.user["id"], "Acme Operations")

    def tearDown(self):
        self.connection.close()
        self.tmp.cleanup()

    def test_local_generator_creates_safe_files_for_business_categories(self):
        for category, prompt in (
            ("internal", "Build a CRM for our sales team"),
            ("customer", "Build a client portal for project updates"),
            ("marketing", "Build a marketing site for a plumbing business"),
            ("mobile", "Build a mobile-ready field service workflow"),
        ):
            with self.subTest(category=category):
                generated = generate_project(prompt, category)
                self.assertIn("index.html", generated["files"])
                self.assertIn("styles.css", generated["files"])
                self.assertIn("app.js", generated["files"])
                self.assertTrue(generated["name"])
                self.assertTrue(generated["summary"])
                for path, content in generated["files"].items():
                    self.assertNotIn("..", Path(path).parts)
                    self.assertNotIn("<script", path.lower())
                    self.assertIsInstance(content, str)

    def test_create_build_edit_preview_and_publish_have_immutable_versions(self):
        project = self.service.create_project(
            self.user["id"],
            self.workspace["id"],
            "Build an operations dashboard for our team",
            "internal",
        )
        first_version = project["current_version_id"]
        self.assertEqual(project["status"], "draft")
        self.assertEqual(len(project["files"]), 3)

        rebuilt = self.service.build_project(
            self.user["id"], project["id"], "Build an inventory tracker for our warehouse"
        )
        self.assertNotEqual(rebuilt["current_version_id"], first_version)
        self.assertEqual(len(self.service.list_versions(self.user["id"], project["id"])), 2)

        edited = self.service.update_file(
            self.user["id"], project["id"], "index.html", "<!doctype html><title>Edited Arin app</title>"
        )
        self.assertEqual(edited["version_number"], 3)
        html, content_type, headers = self.service.read_preview(project["id"])
        self.assertEqual(content_type, "text/html; charset=utf-8")
        self.assertIn(b"Edited Arin app", html)
        self.assertIn("sandbox", headers["Content-Security-Policy"])

        deployment = self.service.publish_project(self.user["id"], project["id"])
        self.assertEqual(deployment["status"], "published")
        published_html, _, _ = self.service.read_published(deployment["slug"])
        self.assertIn(b"Edited Arin app", published_html)

        restored = self.service.restore_version(self.user["id"], project["id"], first_version)
        self.assertEqual(restored["version_number"], 4)
        self.assertIn(b"operations dashboard", self.service.read_preview(project["id"])[0])

        self.service.unpublish_project(self.user["id"], project["id"])
        with self.assertRaises(NotFoundError):
            self.service.read_published(deployment["slug"])

    def test_file_paths_are_normalized_and_traversal_is_rejected(self):
        project = self.service.create_project(
            self.user["id"], self.workspace["id"], "Build a CRM", "internal"
        )
        with self.assertRaises(ValidationError):
            self.service.update_file(
                self.user["id"], project["id"], "../../secret.txt", "not safe"
            )


if __name__ == "__main__":
    unittest.main()
