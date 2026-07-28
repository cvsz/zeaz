import json
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import app


class CatalogCouponMutationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        root = Path(self.tmp.name)
        app.DATA, app.DB_PATH = root / "data", root / "data" / "catalog.sqlite3"
        self.previous_admin = app.ADMIN_KEY
        app.ADMIN_KEY = "test-admin"
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
        app.ADMIN_KEY = self.previous_admin
        self.tmp.cleanup()

    def request(self, path, method, payload, *, admin=False):
        request = Request(
            self.base + path,
            data=json.dumps(payload, separators=(",", ":")).encode(),
            method=method,
            headers={
                "Content-Type": "application/json",
                **({"X-Admin-Key": "test-admin"} if admin else {}),
            },
        )
        try:
            with urlopen(request, timeout=3) as response:
                return response.status, json.loads(response.read())
        except HTTPError as error:
            status = error.code
            result = json.loads(error.read())
            error.close()
            return status, result

    def concurrent(self, call):
        barrier = threading.Barrier(2)

        def invoke(index):
            barrier.wait(timeout=3)
            return call(index)

        with ThreadPoolExecutor(max_workers=2) as pool:
            return list(pool.map(invoke, range(2)))

    def test_concurrent_menu_partial_updates_do_not_overwrite_each_other(self):
        results = self.concurrent(
            lambda index: self.request(
                "/api/admin/menu/classic",
                "PATCH",
                {"price": 25} if index == 0 else {"available": False},
                admin=True,
            )
        )
        self.assertEqual([status for status, _ in results], [200, 200])
        with app.db() as connection:
            item = connection.execute(
                "SELECT price,available FROM menu_items WHERE id='classic'"
            ).fetchone()
            events = connection.execute(
                """SELECT details FROM audit_logs
                   WHERE entity_id='classic' AND action='update'
                   ORDER BY id"""
            ).fetchall()
        self.assertEqual(dict(item), {"price": 25, "available": 0})
        self.assertEqual(
            {tuple(json.loads(event["details"])["keys"]) for event in events},
            {("price",), ("available",)},
        )

    def test_menu_rejects_unknown_only_payload_without_audit(self):
        status, _ = self.request(
            "/api/admin/menu/classic",
            "PATCH",
            {"unknown": "ignored"},
            admin=True,
        )
        self.assertEqual(status, 400)
        with app.db() as connection:
            audits = connection.execute(
                """SELECT COUNT(*) FROM audit_logs
                   WHERE entity_id='classic' AND action='update'"""
            ).fetchone()[0]
        self.assertEqual(audits, 0)

    def test_coupon_rejects_invalid_code_and_time_windows(self):
        future = datetime.now(timezone.utc) + timedelta(days=2)
        payloads = [
            {"code": "SAVE!", "starts_at": "", "ends_at": ""},
            {"code": "SAVE10", "starts_at": "2026-07-29T10:00:00", "ends_at": ""},
            {
                "code": "SAVE10",
                "starts_at": future.isoformat(),
                "ends_at": (future - timedelta(hours=1)).isoformat(),
            },
        ]
        for payload in payloads:
            status, _ = self.request(
                "/api/admin/coupons",
                "POST",
                {
                    "kind": "fixed",
                    "value": 10,
                    "minimum_order": 0,
                    "maximum_uses": 1,
                    **payload,
                },
                admin=True,
            )
            self.assertEqual(status, 400)
        with app.db() as connection:
            self.assertEqual(
                connection.execute("SELECT COUNT(*) FROM coupons").fetchone()[0],
                0,
            )

    def test_coupon_window_is_stored_as_canonical_utc(self):
        starts_at = datetime.now(timezone.utc) + timedelta(hours=1)
        ends_at = starts_at + timedelta(days=1)
        status, result = self.request(
            "/api/admin/coupons",
            "POST",
            {
                "code": "TIMED10",
                "kind": "fixed",
                "value": 10,
                "minimum_order": 50,
                "maximum_uses": 10,
                "starts_at": starts_at.astimezone(
                    timezone(timedelta(hours=7))
                ).isoformat(),
                "ends_at": ends_at.isoformat().replace("+00:00", "Z"),
            },
            admin=True,
        )
        self.assertEqual(status, 201)
        self.assertEqual(result["coupon"]["starts_at"], starts_at.isoformat())
        self.assertEqual(result["coupon"]["ends_at"], ends_at.isoformat())

    def test_concurrent_duplicate_coupon_creation_has_one_audit(self):
        payload = {
            "code": "ONCE10",
            "kind": "fixed",
            "value": 10,
            "minimum_order": 0,
            "maximum_uses": 1,
        }
        results = self.concurrent(
            lambda _: self.request(
                "/api/admin/coupons", "POST", payload, admin=True
            )
        )
        self.assertEqual(sorted(status for status, _ in results), [201, 400])
        with app.db() as connection:
            coupons = connection.execute(
                "SELECT COUNT(*) FROM coupons WHERE code='ONCE10'"
            ).fetchone()[0]
            audits = connection.execute(
                """SELECT COUNT(*) FROM audit_logs
                   WHERE entity_type='coupon' AND action='create'"""
            ).fetchone()[0]
        self.assertEqual(coupons, 1)
        self.assertEqual(audits, 1)

    def test_coupon_limit_is_enforced_across_concurrent_orders(self):
        now = app.utcnow()
        with app.db() as connection:
            connection.execute(
                "INSERT INTO coupons VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (
                    "CPN-LIMIT1",
                    "LIMIT1",
                    "fixed",
                    1,
                    0,
                    1,
                    0,
                    "",
                    "",
                    1,
                    now,
                ),
            )

        pickup_date = date.today().isoformat()

        def order(index):
            return self.request(
                "/api/orders",
                "POST",
                {
                    "name": f"Customer {index}",
                    "phone": f"081234567{index}",
                    "pickup_date": pickup_date,
                    "pickup_slot": app.DEFAULT_SETTINGS["pickup_slots"][0],
                    "payment_method": "cash",
                    "items": [{"id": "classic", "quantity": 1}],
                    "coupon_code": "LIMIT1",
                },
            )

        results = self.concurrent(order)
        self.assertEqual(sorted(status for status, _ in results), [201, 400])
        with app.db() as connection:
            coupon = connection.execute(
                "SELECT used_count FROM coupons WHERE id='CPN-LIMIT1'"
            ).fetchone()
            orders = connection.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
            redemptions = connection.execute(
                "SELECT COUNT(*) FROM coupon_redemptions"
            ).fetchone()[0]
        self.assertEqual(coupon["used_count"], 1)
        self.assertEqual(orders, 1)
        self.assertEqual(redemptions, 1)


if __name__ == "__main__":
    unittest.main()
