import os
import subprocess
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import app


ROOT = Path(__file__).resolve().parents[1]


class BackupRestoreTests(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory()
        root = Path(self.temporary.name)
        app.DATA = root / "data"
        app.DB_PATH = app.DATA / "source.sqlite3"
        self.backups = root / "backups"
        app.initialise_database()

    def tearDown(self):
        self.temporary.cleanup()

    def run_script(self, script, *arguments):
        return subprocess.run(
            ["bash", str(ROOT / "scripts" / script), *map(str, arguments)],
            cwd=ROOT,
            env={
                **os.environ,
                "DATABASE_PATH": str(app.DB_PATH),
                "BACKUP_DIR": str(self.backups),
            },
            capture_output=True,
            text=True,
        )

    def test_plain_backup_passes_isolated_restore_drill(self):
        backup = self.run_script("backup-database.sh")
        self.assertEqual(backup.returncode, 0, backup.stderr)
        candidates = list(self.backups.glob("*.sqlite3"))
        self.assertEqual(len(candidates), 1)

        drill = self.run_script("restore-drill.sh", candidates[0])
        self.assertEqual(drill.returncode, 0, drill.stderr)
        self.assertIn("Restore drill passed", drill.stdout)

    def test_restore_drill_rejects_checksum_mismatch(self):
        backup = self.run_script("backup-database.sh")
        self.assertEqual(backup.returncode, 0, backup.stderr)
        candidate = next(self.backups.glob("*.sqlite3"))
        candidate.write_bytes(candidate.read_bytes() + b"corrupt")

        drill = self.run_script("restore-drill.sh", candidate)
        self.assertNotEqual(drill.returncode, 0)
        self.assertIn("FAILED", drill.stdout + drill.stderr)


if __name__ == "__main__":
    unittest.main()
