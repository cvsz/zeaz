import json
import threading
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import app


class SettlementReceiptTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        root = Path(self.tmp.name)
        app.DATA, app.DB_PATH = root / "data", root / "data" / "settlement.sqlite3"
        self.keys = (app.ADMIN_KEY, app.EMPLOYEE_KEY)
        app.ADMIN_KEY = "test-admin"
        app.EMPLOYEE_KEY = "test-employee"
        app.RATE_BUCKETS.clear()
        app.initialise_database()
        self.server = app.BoundedHTTPServer(("127.0.0.1", 0), app.Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        app.ADMIN_KEY, app.EMPLOYEE_KEY = self.keys
        self.tmp.cleanup()

    def request(self, path, method, payload, headers=None):
        request = Request(
            self.base + path,
            data=json.dumps(payload, separators=(",", ":")).encode(),
            method=method,
            headers={"Content-Type": "application/json", **(headers or {})},
        )
        try:
            with urlopen(request, timeout=3) as response:
                return response.status, json.loads(response.read())
        except HTTPError as error:
            status = error.code
            result = json.loads(error.read())
            error.close()
            return status, result

    def seed_order(self, *, delivery=False, payment_status="pending"):
        now = app.utcnow()
        with app.db() as connection:
            connection.execute(
                "INSERT INTO customers VALUES (?,?,?,?,?)",
                ("0812345678", "Settlement Test", 0, now, now),
            )
            connection.execute(
                "INSERT INTO orders VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (
                    "MPP-SETTLEMENT",
                    now,
                    "ready",
                    "Settlement Test",
                    "0812345678",
                    "2026-07-29",
                    "09:00-10:00",
                    107,
                    "",
                    "cash",
                    payment_status,
                ),
            )
            connection.execute(
                """INSERT INTO order_items(
                     order_id,menu_item_id,name,quantity,unit_price
                   ) VALUES (?,?,?,?,?)""",
                ("MPP-SETTLEMENT", "classic", "Classic", 11, 10),
            )
            connection.execute(
                "INSERT INTO order_financials VALUES (?,?,?,?,?,?,?,?)",
                ("MPP-SETTLEMENT", 110, 7, 10, 107, "", 4, 0),
            )
            if delivery:
                connection.execute(
                    "INSERT INTO riders VALUES (?,?,?,?,?,?,?)",
                    ("RDR-SETTLE", "Rider", "0899999999", 1, 1, now, now),
                )
                connection.execute(
                    """INSERT INTO deliveries(
                         order_id,zone_id,recipient_name,recipient_phone,address,
                         rider_id,status,tracking_code,assigned_at,updated_at
                       ) VALUES (?,?,?,?,?,?,?,?,?,?)""",
                    (
                        "MPP-SETTLEMENT",
                        "central",
                        "Settlement Test",
                        "0812345678",
                        "Bangkok",
                        "RDR-SETTLE",
                        "on_the_way",
                        "TRK-SETTLEMENT",
                        now,
                        now,
                    ),
                )

    def test_completion_requires_payment_but_accepts_atomic_paid_transition(self):
        self.seed_order()
        endpoint = "/api/admin/orders/MPP-SETTLEMENT"
        headers = {"X-Admin-Key": "test-admin"}
        status, _ = self.request(endpoint, "PATCH", {"status": "completed"}, headers)
        self.assertEqual(status, 400)

        status, result = self.request(
            endpoint,
            "PATCH",
            {"status": "completed", "payment_status": "paid"},
            headers,
        )
        self.assertEqual(status, 200)
        self.assertEqual(result["order"]["status"], "completed")
        self.assertEqual(result["order"]["payment"]["status"], "paid")
        with app.db() as connection:
            completion_events = connection.execute(
                """SELECT COUNT(*) FROM order_history
                   WHERE order_id='MPP-SETTLEMENT' AND status='completed'"""
            ).fetchone()[0]
            loyalty_events = connection.execute(
                """SELECT COUNT(*) FROM loyalty_ledger
                   WHERE order_id='MPP-SETTLEMENT'
                     AND reason='order_completed'"""
            ).fetchone()[0]
        self.assertEqual(completion_events, 1)
        self.assertEqual(loyalty_events, 1)

    def test_delivery_settlement_requires_paid_order(self):
        self.seed_order(delivery=True)
        endpoint = "/api/staff/deliveries/MPP-SETTLEMENT"
        headers = {"X-Employee-Key": "test-employee"}
        status, _ = self.request(endpoint, "PATCH", {"status": "delivered"}, headers)
        self.assertEqual(status, 400)
        with app.db() as connection:
            delivery_status = connection.execute(
                "SELECT status FROM deliveries WHERE order_id='MPP-SETTLEMENT'"
            ).fetchone()[0]
            connection.execute(
                """UPDATE orders SET payment_status='paid'
                   WHERE id='MPP-SETTLEMENT'"""
            )
        self.assertEqual(delivery_status, "on_the_way")

        status, result = self.request(
            endpoint, "PATCH", {"status": "delivered"}, headers
        )
        self.assertEqual(status, 200)
        self.assertEqual(result["order"]["status"], "completed")
        with app.db() as connection:
            delivery = connection.execute(
                """SELECT status,delivered_at FROM deliveries
                   WHERE order_id='MPP-SETTLEMENT'"""
            ).fetchone()
        self.assertEqual(delivery["status"], "delivered")
        self.assertTrue(delivery["delivered_at"])

    def test_receipt_requires_payment_and_is_idempotent(self):
        self.seed_order()
        endpoint = "/api/admin/orders/MPP-SETTLEMENT/receipt"
        headers = {"X-Admin-Key": "test-admin"}
        status, _ = self.request(endpoint, "POST", {}, headers)
        self.assertEqual(status, 400)
        with app.db() as connection:
            connection.execute(
                """UPDATE orders SET payment_status='paid'
                   WHERE id='MPP-SETTLEMENT'"""
            )

        first_status, first = self.request(
            endpoint,
            "POST",
            {"customer_tax_name": "Buyer", "customer_tax_id": "1234567890123"},
            headers,
        )
        second_status, second = self.request(endpoint, "POST", {}, headers)
        self.assertEqual(first_status, 201)
        self.assertEqual(second_status, 200)
        self.assertEqual(first["receipt"]["id"], second["receipt"]["id"])
        self.assertEqual(first["receipt"]["subtotal"], 110)
        self.assertEqual(first["receipt"]["discount"], 10)
        self.assertEqual(first["receipt"]["delivery_fee"], 7)
        self.assertEqual(first["receipt"]["total"], 107)
        with app.db() as connection:
            self.assertEqual(
                connection.execute("SELECT COUNT(*) FROM pos_receipts").fetchone()[0],
                1,
            )

    def test_tax_invoice_uses_receipt_snapshot_and_is_idempotent(self):
        self.seed_order(payment_status="paid")
        headers = {"X-Admin-Key": "test-admin"}
        _, receipt = self.request(
            "/api/admin/orders/MPP-SETTLEMENT/receipt", "POST", {}, headers
        )
        receipt_id = receipt["receipt"]["id"]
        with app.db() as connection:
            app.set_setting(
                connection,
                "business_profile",
                {
                    "legal_name": "MooPiew Co., Ltd.",
                    "tax_id": "1234567890123",
                    "address": "Bangkok",
                    "branch": "Head Office",
                    "vat_registered": True,
                    "vat_rate": 7,
                },
            )
            connection.execute(
                "UPDATE orders SET total=999 WHERE id='MPP-SETTLEMENT'"
            )

        endpoint = f"/api/admin/receipts/{receipt_id}/tax-invoice"
        first_status, first = self.request(
            endpoint,
            "POST",
            {"buyer_name": "Buyer", "buyer_tax_id": "9876543210987"},
            headers,
        )
        second_status, second = self.request(
            endpoint, "POST", {"buyer_name": "Changed"}, headers
        )
        self.assertEqual(first_status, 201)
        self.assertEqual(second_status, 200)
        invoice = first["tax_invoice"]
        self.assertEqual(second["tax_invoice"]["tax_invoice_number"], invoice["tax_invoice_number"])
        self.assertEqual(invoice["total"], 107)
        self.assertEqual(invoice["amount_before_vat"], 100)
        self.assertEqual(invoice["vat_amount"], 7)
        self.assertEqual(invoice["seller_tax_id"], "1234567890123")


if __name__ == "__main__":
    unittest.main()
