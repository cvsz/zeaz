import sqlite3
import threading
import time
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import app


class DatabaseTransactionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory()
        root = Path(self.temporary.name)
        app.DATA = root / "data"
        app.DB_PATH = app.DATA / "transactions.sqlite3"
        app.initialise_database()

    def tearDown(self):
        self.temporary.cleanup()

    def test_immediate_transactions_serialize_independent_connections(self):
        entered = threading.Event()
        completed = threading.Event()
        elapsed = []

        def competing_writer():
            entered.set()
            started = time.monotonic()
            with app.db(immediate=True) as connection:
                connection.execute(
                    "UPDATE settings SET value=value WHERE key='store_name'"
                )
            elapsed.append(time.monotonic() - started)
            completed.set()

        with app.db(immediate=True) as connection:
            worker = threading.Thread(target=competing_writer)
            worker.start()
            self.assertTrue(entered.wait(1))
            time.sleep(0.1)
            self.assertFalse(completed.is_set())
            connection.execute(
                "UPDATE settings SET value=value WHERE key='store_name'"
            )
        worker.join(2)
        self.assertFalse(worker.is_alive())
        self.assertGreaterEqual(elapsed[0], 0.09)

    def test_inventory_consumption_is_unique_per_order_and_item(self):
        with app.db(immediate=True) as connection:
            now = app.utcnow()
            connection.execute(
                """INSERT INTO inventory_items
                VALUES ('INV-TEST','Test stock','unit',10,0,1,?,?)""",
                (now, now),
            )
            connection.execute(
                """INSERT INTO orders VALUES
                ('MPP-TEST',?,'new','Test','0812345678','2099-01-01',
                '09:00',10,'','cash','pending')""",
                (now,),
            )
            movement = (
                "MOV-ONE",
                "INV-TEST",
                -1,
                "order_completed",
                "MPP-TEST",
                "",
                now,
                "test",
            )
            connection.execute(
                "INSERT INTO inventory_movements VALUES (?,?,?,?,?,?,?,?)",
                movement,
            )
            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute(
                    "INSERT INTO inventory_movements VALUES (?,?,?,?,?,?,?,?)",
                    ("MOV-TWO", *movement[1:]),
                )


if __name__ == "__main__":
    unittest.main()
