import base64
import json
import threading
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import app


class ZerpAccountingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        root = Path(self.tmp.name)
        app.DATA, app.DB_PATH = root / "data", root / "data" / "zerp.sqlite3"
        self.old_key = app.ADMIN_KEY
        app.ADMIN_KEY = "zerp-test-admin"
        app.RATE_BUCKETS.clear()
        app.initialise_database()
        with app.db() as connection:
            connection.execute(
                "INSERT INTO pos_receipts VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                ("RCT-ZERP", "MPP-ZERP", "MP-ZERP", "", "", 100, 10, 20, 110, app.utcnow(), "admin"),
            )
        self.server = app.BoundedHTTPServer(("127.0.0.1", 0), app.Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        app.ADMIN_KEY = self.old_key
        self.tmp.cleanup()

    def request(self, headers=None):
        request = Request(self.base + "/api/admin/zerp/accounting/entries", headers=headers or {})
        try:
            with urlopen(request, timeout=3) as response:
                return response.status, json.loads(response.read())
        except HTTPError as error:
            payload = json.loads(error.read())
            error.close()
            return error.code, payload

    def test_requires_owner_key(self):
        status, body = self.request()
        self.assertEqual(status, 401)
        self.assertIn("error", body)

    def test_projects_receipt_to_balanced_double_entry(self):
        headers = {"X-Admin-Key-B64": base64.b64encode(b"zerp-test-admin").decode()}
        status, body = self.request(headers)
        self.assertEqual(status, 200)
        self.assertEqual(body["currency"], "THB")
        self.assertEqual(len(body["entries"]), 1)
        entry = body["entries"][0]
        self.assertTrue(entry["balanced"])
        self.assertEqual(entry["total_debit"], 110)
        self.assertEqual(entry["total_credit"], 110)
        self.assertEqual(len(entry["lines"]), 3)

        # Projection is idempotent when the endpoint is retried. The retry also
        # provides a transaction barrier: Handler.do_GET serializes the first
        # response while its db() context is still committing the projection.
        status, again = self.request(headers)
        self.assertEqual(status, 200)
        self.assertEqual(again["entries"][0]["id"], entry["id"])

        with app.db() as connection:
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM ledger_entries").fetchone()[0], 1)
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM ledger_lines").fetchone()[0], 3)

    def test_inventory_moves_are_owner_only_and_projected(self):
        now = app.utcnow()
        with app.db() as connection:
            connection.execute(
                "INSERT INTO inventory_items VALUES (?,?,?,?,?,?,?,?)",
                ("INV-ZERP", "Pork", "kg", 4, 1, 1, now, now),
            )
            connection.execute(
                "INSERT INTO inventory_movements VALUES (?,?,?,?,?,?,?,?)",
                ("MOV-ZERP", "INV-ZERP", -2, "order_completed", None, "recipe", now, "admin"),
            )
        headers = {"X-Admin-Key-B64": base64.b64encode(b"zerp-test-admin").decode()}
        request = Request(self.base + "/api/admin/zerp/inventory/moves", headers=headers)
        with urlopen(request, timeout=3) as response:
            body = json.loads(response.read())
        self.assertEqual(body["moves"][0]["id"], "MOV-ZERP")
        self.assertEqual(body["moves"][0]["source_location"], "stock")
        self.assertEqual(body["moves"][0]["destination_location"], "consumption")


if __name__ == "__main__":
    unittest.main()
