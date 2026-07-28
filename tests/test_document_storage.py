import hashlib
import json
import os
import subprocess
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from cryptography.fernet import Fernet

import app


ROOT = Path(__file__).resolve().parents[1]


class DocumentStorageTests(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory()
        root = Path(self.temporary.name)
        app.DATA = root / "data"
        app.DB_PATH = app.DATA / "documents.sqlite3"
        self.key = Fernet.generate_key().decode()
        self.environment = root / "document.env"
        self.environment.write_text(
            "\n".join(
                [
                    f"DATA_DIR={app.DATA}",
                    f"DATABASE_PATH={app.DB_PATH}",
                    f"DOCUMENT_ENCRYPTION_KEY={self.key}",
                    "DELETED_DOCUMENT_RETENTION_DAYS=30",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        app.initialise_database()
        documents = app.DATA / "documents"
        documents.mkdir(mode=0o700)
        self.plaintext = documents / "DOC-LEGACY.png"
        self.raw = b"\x89PNG\r\n\x1a\nlegacy-sensitive"
        self.plaintext.write_bytes(self.raw)
        now = app.utcnow()
        with app.db(immediate=True) as connection:
            connection.execute(
                """INSERT INTO uploaded_documents(
                id,provider_id,subject_type,subject_id,requirement_id,
                original_filename,storage_path,mime_type,size_bytes,sha256,
                status,metadata,created_at,updated_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    "DOC-LEGACY",
                    "provider-grab",
                    "rider",
                    "RDR-LEGACY",
                    "grab-rider-national-id",
                    "legacy.png",
                    str(self.plaintext),
                    "image/png",
                    len(self.raw),
                    hashlib.sha256(self.raw).hexdigest(),
                    "pending",
                    json.dumps({"uploaded_by": "legacy"}),
                    now,
                    now,
                ),
            )

    def tearDown(self):
        self.temporary.cleanup()

    def command(self, *arguments):
        return subprocess.run(
            ["bash", str(ROOT / "scripts/document-storage.sh"), *arguments],
            cwd=ROOT,
            env={
                **os.environ,
                "MOOPIEW_ENV_FILE": str(self.environment),
            },
            capture_output=True,
            text=True,
        )

    def test_migrate_then_purge_with_dry_run_guards(self):
        dry_run = self.command("migrate", "--dry-run")
        self.assertEqual(dry_run.returncode, 0, dry_run.stderr)
        self.assertTrue(self.plaintext.exists())

        migration = self.command("migrate")
        self.assertEqual(migration.returncode, 0, migration.stderr)
        with app.db() as connection:
            row = connection.execute(
                "SELECT storage_path,metadata FROM uploaded_documents WHERE id='DOC-LEGACY'"
            ).fetchone()
        encrypted = Path(row["storage_path"])
        self.assertFalse(self.plaintext.exists())
        self.assertEqual(
            Fernet(self.key.encode()).decrypt(encrypted.read_bytes()), self.raw
        )
        self.assertEqual(
            json.loads(row["metadata"])["storage_encryption"], "fernet-v1"
        )

        with app.db(immediate=True) as connection:
            connection.execute(
                """UPDATE uploaded_documents
                SET status='deleted',updated_at='2000-01-01T00:00:00+00:00'
                WHERE id='DOC-LEGACY'"""
            )
        dry_purge = self.command("purge", "--retention-days", "30", "--dry-run")
        self.assertEqual(dry_purge.returncode, 0, dry_purge.stderr)
        self.assertTrue(encrypted.exists())

        purge = self.command("purge", "--retention-days", "30")
        self.assertEqual(purge.returncode, 0, purge.stderr)
        self.assertFalse(encrypted.exists())
        with app.db() as connection:
            count = connection.execute(
                "SELECT COUNT(*) FROM uploaded_documents WHERE id='DOC-LEGACY'"
            ).fetchone()[0]
        self.assertEqual(count, 0)

    def test_supported_retention_timer_invokes_the_canonical_tool(self):
        service = (
            ROOT / "deploy/systemd/moopiew-document-retention.service"
        ).read_text(encoding="utf-8")
        timer = (
            ROOT / "deploy/systemd/moopiew-document-retention.timer"
        ).read_text(encoding="utf-8")
        dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
        self.assertIn("scripts/document-storage.py purge", service)
        self.assertIn("OnCalendar=daily", timer)
        self.assertIn("Persistent=true", timer)
        self.assertIn(
            "scripts/document-storage.py ./scripts/document-storage.py", dockerfile
        )


if __name__ == "__main__":
    unittest.main()
