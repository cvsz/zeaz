import shutil
import sqlite3
import tempfile
import threading
import unittest
from pathlib import Path

from migrations.runner import MIGRATIONS, MigrationError, apply_migrations


class MigrationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.database = Path(self.temporary.name) / "database.sqlite3"
        self.connection = sqlite3.connect(self.database)

    def tearDown(self):
        self.connection.close()
        self.temporary.cleanup()

    def test_fresh_database_and_idempotence(self):
        self.assertEqual(apply_migrations(self.connection), [0, 1, 2, 3])
        versions = self.connection.execute(
            "SELECT version FROM schema_migrations ORDER BY version"
        ).fetchall()
        self.assertEqual(versions, [(0,), (1,), (2,), (3,)])
        columns = {
            row[1] for row in self.connection.execute("PRAGMA table_info(deliveries)")
        }
        self.assertIn("distance_km", columns)
        oauth_columns = {
            row[1] for row in self.connection.execute("PRAGMA table_info(oauth_states)")
        }
        self.assertIn("verifier_cipher", oauth_columns)
        payment_sql = self.connection.execute(
            "SELECT sql FROM sqlite_master WHERE name='payment_attempts'"
        ).fetchone()[0]
        self.assertIn("'refunded'", payment_sql)
        self.assertEqual(apply_migrations(self.connection), [])
        self.assertEqual(
            self.connection.execute("PRAGMA foreign_key_check").fetchall(), []
        )

    def test_legacy_payment_table_is_rebuilt_without_data_loss(self):
        self.connection.executescript(
            """
            PRAGMA foreign_keys=OFF;
            CREATE TABLE orders (
              id TEXT PRIMARY KEY, created_at TEXT NOT NULL, status TEXT NOT NULL,
              customer_name TEXT NOT NULL, customer_phone TEXT NOT NULL,
              pickup_date TEXT NOT NULL, pickup_slot TEXT NOT NULL,
              total INTEGER NOT NULL, notes TEXT NOT NULL DEFAULT '',
              payment_method TEXT NOT NULL, payment_status TEXT NOT NULL DEFAULT 'pending'
            );
            INSERT INTO orders VALUES (
              'ORDER-1','now','new','A','0800000000','2026-07-28','09:00',
              10,'','cash','paid'
            );
            CREATE TABLE payment_attempts (
              id TEXT PRIMARY KEY,
              order_id TEXT NOT NULL REFERENCES orders(id),
              provider TEXT NOT NULL,
              provider_reference TEXT NOT NULL UNIQUE,
              provider_order_id TEXT UNIQUE,
              amount INTEGER NOT NULL,
              status TEXT NOT NULL CHECK(status IN ('created','pending','paid','failed','expired','cancelled')),
              qr_image TEXT NOT NULL DEFAULT '',
              qr_type TEXT NOT NULL DEFAULT '',
              expires_at TEXT NOT NULL DEFAULT '',
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL,
              confirmed_at TEXT NOT NULL DEFAULT '',
              provider_response TEXT NOT NULL DEFAULT '{}'
            );
            INSERT INTO payment_attempts(
              id,order_id,provider,provider_reference,amount,status,created_at,updated_at
            ) VALUES ('PAY-1','ORDER-1','test','REF-1',10,'paid','now','now');
            """
        )
        apply_migrations(self.connection)
        row = self.connection.execute(
            "SELECT id,status FROM payment_attempts"
        ).fetchone()
        self.assertEqual(row, ("PAY-1", "paid"))
        self.connection.execute(
            "UPDATE payment_attempts SET status='refunded' WHERE id='PAY-1'"
        )

    def test_legacy_delivery_gets_distance_column(self):
        self.connection.executescript(
            """
            CREATE TABLE deliveries (
              order_id TEXT PRIMARY KEY,
              zone_id TEXT NOT NULL,
              recipient_name TEXT NOT NULL,
              recipient_phone TEXT NOT NULL,
              address TEXT NOT NULL,
              landmark TEXT NOT NULL DEFAULT '',
              rider_id TEXT,
              status TEXT NOT NULL DEFAULT 'queued',
              tracking_code TEXT NOT NULL UNIQUE,
              assigned_at TEXT NOT NULL DEFAULT '',
              picked_up_at TEXT NOT NULL DEFAULT '',
              delivered_at TEXT NOT NULL DEFAULT '',
              updated_at TEXT NOT NULL
            );
            INSERT INTO deliveries(
              order_id,zone_id,recipient_name,recipient_phone,address,tracking_code,updated_at
            ) VALUES ('ORDER-1','central','A','0800000000','Road','TRACK-1','now');
            """
        )
        apply_migrations(self.connection)
        row = self.connection.execute(
            "SELECT tracking_code,distance_km FROM deliveries"
        ).fetchone()
        self.assertEqual(row, ("TRACK-1", 0.0))

    def test_pkce_migration_invalidates_legacy_oauth_states(self):
        directory = Path(self.temporary.name) / "pre_pkce"
        directory.mkdir()
        for name in (
            "000_core_schema.sql",
            "001_provider_document_requirements.sql",
            "002_legacy_schema.py",
        ):
            shutil.copy(MIGRATIONS / name, directory / name)
        apply_migrations(self.connection, directory)
        self.connection.execute(
            "INSERT INTO oauth_states(state,expires_at) VALUES ('legacy','2099-01-01')"
        )
        self.connection.commit()
        shutil.copy(
            MIGRATIONS / "003_oauth_pkce.py", directory / "003_oauth_pkce.py"
        )
        self.assertEqual(apply_migrations(self.connection, directory), [3])
        columns = {
            row[1] for row in self.connection.execute("PRAGMA table_info(oauth_states)")
        }
        self.assertIn("verifier_cipher", columns)
        self.assertEqual(
            self.connection.execute("SELECT COUNT(*) FROM oauth_states").fetchone()[0],
            0,
        )

    def test_changed_applied_migration_fails_closed(self):
        directory = Path(self.temporary.name) / "migrations"
        shutil.copytree(MIGRATIONS, directory)
        apply_migrations(self.connection, directory)
        with (directory / "000_core_schema.sql").open("a", encoding="utf-8") as file:
            file.write("\n-- changed\n")
        with self.assertRaises(MigrationError):
            apply_migrations(self.connection, directory)

    def test_failed_sql_migration_is_atomic(self):
        directory = Path(self.temporary.name) / "broken"
        directory.mkdir()
        (directory / "000_broken.sql").write_text(
            "CREATE TABLE should_rollback(id INTEGER); INVALID SQL;",
            encoding="utf-8",
        )
        with self.assertRaises(sqlite3.DatabaseError):
            apply_migrations(self.connection, directory)
        self.assertIsNone(
            self.connection.execute(
                "SELECT 1 FROM sqlite_master WHERE name='should_rollback'"
            ).fetchone()
        )
        self.assertEqual(
            self.connection.execute("SELECT COUNT(*) FROM schema_migrations").fetchone()[0],
            0,
        )

    def test_concurrent_startup_applies_each_version_once(self):
        self.connection.close()
        errors = []

        def migrate():
            connection = None
            try:
                connection = sqlite3.connect(self.database, timeout=10)
                apply_migrations(connection)
            except Exception as error:
                errors.append(error)
            finally:
                if connection is not None:
                    connection.close()

        threads = [threading.Thread(target=migrate) for _ in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.connection = sqlite3.connect(self.database)
        self.assertEqual(errors, [])
        rows = self.connection.execute(
            "SELECT version,COUNT(*) FROM schema_migrations GROUP BY version"
        ).fetchall()
        self.assertEqual(rows, [(0, 1), (1, 1), (2, 1), (3, 1)])


if __name__ == "__main__":
    unittest.main()
