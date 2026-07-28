import json
import threading
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import app


class OrderFinancialLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        root = Path(self.tmp.name)
        app.DATA, app.DB_PATH = root / "data", root / "data" / "orders.sqlite3"
        self.keys = (app.ADMIN_KEY, app.EMPLOYEE_KEY, app.KITCHEN_KEY)
        app.ADMIN_KEY = "test-admin"
        app.EMPLOYEE_KEY = "test-employee"
        app.KITCHEN_KEY = "test-kitchen"
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
        app.ADMIN_KEY, app.EMPLOYEE_KEY, app.KITCHEN_KEY = self.keys
        self.tmp.cleanup()

    def request(self, path, method, payload, headers=None):
        body = json.dumps(payload, separators=(",", ":")).encode()
        request = Request(
            self.base + path,
            data=body,
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

    def seed_order(
        self,
        *,
        order_id="MPP-FINANCE",
        status="new",
        payment_status="pending",
        points_earned=4,
        points_redeemed=0,
        coupon=False,
    ):
        now = app.utcnow()
        phone = "0812345678"
        with app.db() as connection:
            connection.execute(
                "INSERT INTO customers VALUES (?,?,?,?,?)",
                (phone, "Finance Test", 100 - points_redeemed, now, now),
            )
            connection.execute(
                "INSERT INTO orders VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (
                    order_id,
                    now,
                    status,
                    "Finance Test",
                    phone,
                    "2026-07-29",
                    "09:00-10:00",
                    100,
                    "",
                    "cash",
                    payment_status,
                ),
            )
            connection.execute(
                """INSERT INTO order_items(
                     order_id,menu_item_id,name,quantity,unit_price
                   ) VALUES (?,?,?,?,?)""",
                (order_id, "classic", "Classic", 1, 100),
            )
            connection.execute(
                "INSERT INTO order_financials VALUES (?,?,?,?,?,?,?,?)",
                (
                    order_id,
                    110,
                    0,
                    10 if coupon or points_redeemed else 0,
                    100,
                    "SAVE10" if coupon else "",
                    points_earned,
                    points_redeemed,
                ),
            )
            if points_redeemed:
                connection.execute(
                    "INSERT INTO loyalty_ledger VALUES (?,?,?,?,?,?)",
                    (
                        "LOY-REDEEM",
                        phone,
                        -points_redeemed,
                        "order_redeemed",
                        order_id,
                        now,
                    ),
                )
            if coupon:
                connection.execute(
                    "INSERT INTO coupons VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        "CPN-SAVE10",
                        "SAVE10",
                        "fixed",
                        10,
                        0,
                        100,
                        1,
                        "",
                        "",
                        1,
                        now,
                    ),
                )
                connection.execute(
                    "INSERT INTO coupon_redemptions VALUES (?,?,?,?,?)",
                    ("CPN-SAVE10", order_id, phone, 10, now),
                )

    def test_customer_identity_is_required_for_lookup_and_cancel(self):
        self.seed_order()
        for path in ("/api/order-lookup", "/api/orders/MPP-FINANCE/cancel"):
            with self.subTest(path=path):
                status, _ = self.request(
                    path,
                    "POST",
                    {"order_id": "MPP-FINANCE", "phone": "0899999999"},
                )
                self.assertEqual(status, 404)
        with app.db() as connection:
            self.assertEqual(
                connection.execute(
                    "SELECT status FROM orders WHERE id='MPP-FINANCE'"
                ).fetchone()["status"],
                "new",
            )

    def test_cancel_restores_points_and_coupon_exactly_once(self):
        self.seed_order(points_redeemed=10, coupon=True)
        status, result = self.request(
            "/api/orders/MPP-FINANCE/cancel",
            "POST",
            {"phone": "0812345678"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(result["order"]["status"], "cancelled")

        repeated_status, _ = self.request(
            "/api/orders/MPP-FINANCE/cancel",
            "POST",
            {"phone": "0812345678"},
        )
        self.assertEqual(repeated_status, 400)
        with app.db() as connection:
            customer = connection.execute(
                "SELECT points_balance FROM customers WHERE phone='0812345678'"
            ).fetchone()
            coupon = connection.execute(
                "SELECT used_count FROM coupons WHERE id='CPN-SAVE10'"
            ).fetchone()
            restores = connection.execute(
                """SELECT COUNT(*) FROM loyalty_ledger
                   WHERE order_id='MPP-FINANCE'
                     AND reason='order_cancelled_restore'"""
            ).fetchone()[0]
            redemptions = connection.execute(
                "SELECT COUNT(*) FROM coupon_redemptions"
            ).fetchone()[0]
        self.assertEqual(customer["points_balance"], 100)
        self.assertEqual(coupon["used_count"], 0)
        self.assertEqual(restores, 1)
        self.assertEqual(redemptions, 0)

    def test_paid_order_cannot_be_cancelled_by_customer(self):
        self.seed_order(payment_status="paid")
        status, _ = self.request(
            "/api/orders/MPP-FINANCE/cancel",
            "POST",
            {"phone": "0812345678"},
        )
        self.assertEqual(status, 400)
        with app.db() as connection:
            order = connection.execute(
                "SELECT status,payment_status FROM orders WHERE id='MPP-FINANCE'"
            ).fetchone()
        self.assertEqual(dict(order), {"status": "new", "payment_status": "paid"})

    def test_payment_state_cannot_move_backwards(self):
        self.seed_order()
        endpoint = "/api/admin/orders/MPP-FINANCE"
        headers = {"X-Admin-Key": "test-admin"}

        status, _ = self.request(
            endpoint, "PATCH", {"payment_status": "refunded"}, headers
        )
        self.assertEqual(status, 400)
        status, _ = self.request(
            endpoint, "PATCH", {"payment_status": "paid"}, headers
        )
        self.assertEqual(status, 200)
        status, _ = self.request(
            endpoint, "PATCH", {"payment_status": "pending"}, headers
        )
        self.assertEqual(status, 400)
        status, _ = self.request(
            endpoint, "PATCH", {"payment_status": "refunded"}, headers
        )
        self.assertEqual(status, 200)
        status, _ = self.request(
            endpoint, "PATCH", {"payment_status": "paid"}, headers
        )
        self.assertEqual(status, 400)

        with app.db() as connection:
            order = connection.execute(
                "SELECT payment_status FROM orders WHERE id='MPP-FINANCE'"
            ).fetchone()
            changes = connection.execute(
                """SELECT COUNT(*) FROM audit_logs
                   WHERE entity_id='MPP-FINANCE' AND action='payment_change'"""
            ).fetchone()[0]
        self.assertEqual(order["payment_status"], "refunded")
        self.assertEqual(changes, 2)

    def test_staff_cannot_change_financial_state(self):
        self.seed_order()
        status, _ = self.request(
            "/api/staff/orders/MPP-FINANCE",
            "PATCH",
            {"payment_status": "paid"},
            {"X-Employee-Key": "test-employee"},
        )
        self.assertEqual(status, 400)
        status, _ = self.request(
            "/api/admin/orders/MPP-FINANCE",
            "PATCH",
            {"payment_status": "paid"},
            {"X-Employee-Key": "test-employee"},
        )
        self.assertEqual(status, 401)
        with app.db() as connection:
            payment_status = connection.execute(
                "SELECT payment_status FROM orders WHERE id='MPP-FINANCE'"
            ).fetchone()[0]
        self.assertEqual(payment_status, "pending")

    def test_insufficient_inventory_rolls_back_order_and_loyalty(self):
        self.seed_order(points_earned=4)
        now = app.utcnow()
        with app.db() as connection:
            connection.execute(
                "INSERT INTO inventory_items VALUES (?,?,?,?,?,?,?,?)",
                ("INV-PORK", "Pork", "kg", 0.5, 0, 1, now, now),
            )
            connection.execute(
                "INSERT INTO menu_recipes VALUES (?,?,?)",
                ("classic", "INV-PORK", 1),
            )

        status, _ = self.request(
            "/api/admin/orders/MPP-FINANCE",
            "PATCH",
            {"status": "completed"},
            {"X-Admin-Key": "test-admin"},
        )
        self.assertEqual(status, 400)
        with app.db() as connection:
            order_status = connection.execute(
                "SELECT status FROM orders WHERE id='MPP-FINANCE'"
            ).fetchone()[0]
            balance = connection.execute(
                "SELECT points_balance FROM customers WHERE phone='0812345678'"
            ).fetchone()[0]
            completions = connection.execute(
                """SELECT COUNT(*) FROM loyalty_ledger
                   WHERE order_id='MPP-FINANCE'
                     AND reason='order_completed'"""
            ).fetchone()[0]
            stock = connection.execute(
                "SELECT on_hand FROM inventory_items WHERE id='INV-PORK'"
            ).fetchone()[0]
        self.assertEqual(order_status, "new")
        self.assertEqual(balance, 100)
        self.assertEqual(completions, 0)
        self.assertEqual(stock, 0.5)


if __name__ == "__main__":
    unittest.main()
