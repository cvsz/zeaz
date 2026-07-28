import json
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import app


class DeliveryAssignmentTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        root = Path(self.tmp.name)
        app.DATA = root / "data"
        app.DB_PATH = app.DATA / "delivery-assignment.sqlite3"
        self.keys = (app.ADMIN_KEY, app.EMPLOYEE_KEY)
        app.ADMIN_KEY = "test-admin"
        app.EMPLOYEE_KEY = "test-employee"
        app.RATE_BUCKETS.clear()
        app.initialise_database()
        now = app.utcnow()
        with app.db() as connection:
            connection.execute(
                "INSERT INTO customers VALUES (?,?,?,?,?)",
                ("0811111111", "Delivery Customer", 0, now, now),
            )
            connection.executemany(
                "INSERT INTO riders VALUES (?,?,?,?,?,?,?)",
                [
                    ("RDR-ONE", "Rider One", "0822222222", 1, 1, now, now),
                    ("RDR-TWO", "Rider Two", "0833333333", 1, 1, now, now),
                ],
            )
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

    def request(self, path, payload, *, employee=False):
        header = (
            {"X-Employee-Key": "test-employee"}
            if employee
            else {"X-Admin-Key": "test-admin"}
        )
        request = Request(
            self.base + path,
            data=json.dumps(payload, separators=(",", ":")).encode(),
            method="PATCH",
            headers={"Content-Type": "application/json", **header},
        )
        try:
            with urlopen(request, timeout=3) as response:
                return response.status, json.loads(response.read())
        except HTTPError as error:
            status = error.code
            result = json.loads(error.read())
            error.close()
            return status, result

    def seed_delivery(self, order_id, *, payment_status="paid"):
        now = app.utcnow()
        with app.db() as connection:
            connection.execute(
                "INSERT INTO orders VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (
                    order_id,
                    now,
                    "ready",
                    "Delivery Customer",
                    "0811111111",
                    "2026-07-29",
                    "delivery",
                    100,
                    "",
                    "cash",
                    payment_status,
                ),
            )
            connection.execute(
                "INSERT INTO order_financials VALUES (?,?,?,?,?,?,?,?)",
                (order_id, 100, 0, 0, 100, "", 0, 0),
            )
            connection.execute(
                """INSERT INTO deliveries(
                     order_id,zone_id,recipient_name,recipient_phone,address,
                     status,tracking_code,updated_at
                   ) VALUES (?,?,?,?,?,?,?,?)""",
                (
                    order_id,
                    "central",
                    "Delivery Customer",
                    "0811111111",
                    "Bangkok",
                    "queued",
                    f"TRK-{order_id.removeprefix('MPP-')}",
                    now,
                ),
            )

    def test_concurrent_assignment_reserves_rider_once(self):
        self.seed_delivery("MPP-DELIVERY-ONE")
        self.seed_delivery("MPP-DELIVERY-TWO")
        barrier = threading.Barrier(2)

        def assign(order_id):
            barrier.wait(timeout=3)
            return self.request(
                f"/api/admin/deliveries/{order_id}",
                {"rider_id": "RDR-ONE"},
            )

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(
                pool.map(assign, ("MPP-DELIVERY-ONE", "MPP-DELIVERY-TWO"))
            )

        self.assertEqual(sorted(status for status, _ in results), [200, 400])
        with app.db() as connection:
            assigned = connection.execute(
                """SELECT COUNT(*) FROM deliveries
                   WHERE rider_id='RDR-ONE' AND status='assigned'"""
            ).fetchone()[0]
            available = connection.execute(
                "SELECT available FROM riders WHERE id='RDR-ONE'"
            ).fetchone()[0]
            audits = connection.execute(
                """SELECT COUNT(*) FROM audit_logs
                   WHERE entity_type='delivery' AND action='delivery_update'"""
            ).fetchone()[0]
        self.assertEqual(assigned, 1)
        self.assertEqual(available, 0)
        self.assertEqual(audits, 1)

    def test_reassignment_releases_previous_rider(self):
        self.seed_delivery("MPP-DELIVERY-REASSIGN")
        endpoint = "/api/admin/deliveries/MPP-DELIVERY-REASSIGN"
        self.assertEqual(self.request(endpoint, {"rider_id": "RDR-ONE"})[0], 200)
        status, result = self.request(endpoint, {"rider_id": "RDR-TWO"})
        self.assertEqual(status, 200)
        self.assertEqual(result["order"]["fulfillment"]["delivery"]["rider_name"], "Rider Two")
        with app.db() as connection:
            riders = {
                row["id"]: row["available"]
                for row in connection.execute(
                    "SELECT id,available FROM riders ORDER BY id"
                )
            }
        self.assertEqual(riders, {"RDR-ONE": 1, "RDR-TWO": 0})

    def test_staff_cannot_assign_rider(self):
        self.seed_delivery("MPP-DELIVERY-STAFF")
        status, _ = self.request(
            "/api/staff/deliveries/MPP-DELIVERY-STAFF",
            {"rider_id": "RDR-ONE"},
            employee=True,
        )
        self.assertEqual(status, 400)
        with app.db() as connection:
            delivery = connection.execute(
                """SELECT rider_id,status FROM deliveries
                   WHERE order_id='MPP-DELIVERY-STAFF'"""
            ).fetchone()
        self.assertEqual(dict(delivery), {"rider_id": None, "status": "queued"})

    def test_active_rider_cannot_be_manually_marked_available(self):
        self.seed_delivery("MPP-DELIVERY-ACTIVE")
        self.assertEqual(
            self.request(
                "/api/admin/deliveries/MPP-DELIVERY-ACTIVE",
                {"rider_id": "RDR-ONE"},
            )[0],
            200,
        )
        status, _ = self.request(
            "/api/admin/riders/RDR-ONE",
            {"available": True},
        )
        self.assertEqual(status, 400)
        with app.db() as connection:
            available = connection.execute(
                "SELECT available FROM riders WHERE id='RDR-ONE'"
            ).fetchone()[0]
        self.assertEqual(available, 0)

    def test_terminal_delivery_releases_rider(self):
        self.seed_delivery("MPP-DELIVERY-COMPLETE")
        endpoint = "/api/admin/deliveries/MPP-DELIVERY-COMPLETE"
        for payload in (
            {"rider_id": "RDR-ONE"},
            {"status": "picked_up"},
            {"status": "on_the_way"},
            {"status": "delivered"},
        ):
            status, _ = self.request(endpoint, payload)
            self.assertEqual(status, 200)
        with app.db() as connection:
            delivery = connection.execute(
                """SELECT rider_id,status,delivered_at FROM deliveries
                   WHERE order_id='MPP-DELIVERY-COMPLETE'"""
            ).fetchone()
            available = connection.execute(
                "SELECT available FROM riders WHERE id='RDR-ONE'"
            ).fetchone()[0]
        self.assertEqual(delivery["rider_id"], "RDR-ONE")
        self.assertEqual(delivery["status"], "delivered")
        self.assertTrue(delivery["delivered_at"])
        self.assertEqual(available, 1)

    def test_noop_and_combined_assignment_are_rejected(self):
        self.seed_delivery("MPP-DELIVERY-INVALID")
        endpoint = "/api/admin/deliveries/MPP-DELIVERY-INVALID"
        for payload in ({}, {"unknown": True}, {"rider_id": "RDR-ONE", "status": "assigned"}):
            status, _ = self.request(endpoint, payload)
            self.assertEqual(status, 400)
        with app.db() as connection:
            audits = connection.execute(
                """SELECT COUNT(*) FROM audit_logs
                   WHERE entity_id='MPP-DELIVERY-INVALID'"""
            ).fetchone()[0]
        self.assertEqual(audits, 0)


if __name__ == "__main__":
    unittest.main()
