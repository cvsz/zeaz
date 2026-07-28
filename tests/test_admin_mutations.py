import json
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import app


class AdministrativeMutationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        root = Path(self.tmp.name)
        app.DATA, app.DB_PATH = root / "data", root / "data" / "admin.sqlite3"
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

        def invoke(_):
            barrier.wait(timeout=3)
            return call()

        with ThreadPoolExecutor(max_workers=2) as pool:
            return list(pool.map(invoke, range(2)))

    def test_rider_application_can_only_be_approved_once(self):
        now = app.utcnow()
        with app.db() as connection:
            connection.execute(
                """INSERT INTO rider_applications(
                     id,name,phone,vehicle_type,status,created_at
                   ) VALUES (?,?,?,?,?,?)""",
                (
                    "RAP-CONCURRENT",
                    "Concurrent Rider",
                    "0811111111",
                    "motorcycle",
                    "pending",
                    now,
                ),
            )

        results = self.concurrent(
            lambda: self.request(
                "/api/admin/rider-applications/RAP-CONCURRENT",
                "PATCH",
                {"status": "approved"},
                admin=True,
            )
        )
        self.assertEqual(sorted(status for status, _ in results), [200, 400])
        with app.db() as connection:
            application = connection.execute(
                """SELECT status,rider_id FROM rider_applications
                   WHERE id='RAP-CONCURRENT'"""
            ).fetchone()
            riders = connection.execute(
                "SELECT COUNT(*) FROM riders WHERE phone='0811111111'"
            ).fetchone()[0]
            audits = connection.execute(
                """SELECT COUNT(*) FROM audit_logs
                   WHERE entity_id='RAP-CONCURRENT' AND action='approved'"""
            ).fetchone()[0]
        self.assertEqual(application["status"], "approved")
        self.assertTrue(application["rider_id"])
        self.assertEqual(riders, 1)
        self.assertEqual(audits, 1)

    def test_merchant_application_can_only_be_reviewed_once(self):
        now = app.utcnow()
        with app.db() as connection:
            connection.execute(
                """INSERT INTO merchant_applications(
                     id,business_name,owner_name,phone,address,category,
                     status,created_at
                   ) VALUES (?,?,?,?,?,?,?,?)""",
                (
                    "MAP-CONCURRENT",
                    "Concurrent Shop",
                    "Owner",
                    "0822222222",
                    "Bangkok",
                    "restaurant",
                    "pending",
                    now,
                ),
            )

        results = self.concurrent(
            lambda: self.request(
                "/api/admin/merchant-applications/MAP-CONCURRENT",
                "PATCH",
                {"status": "approved"},
                admin=True,
            )
        )
        self.assertEqual(sorted(status for status, _ in results), [200, 400])
        with app.db() as connection:
            application = connection.execute(
                """SELECT status FROM merchant_applications
                   WHERE id='MAP-CONCURRENT'"""
            ).fetchone()
            audits = connection.execute(
                """SELECT COUNT(*) FROM audit_logs
                   WHERE entity_id='MAP-CONCURRENT' AND action='approved'"""
            ).fetchone()[0]
        self.assertEqual(application["status"], "approved")
        self.assertEqual(audits, 1)

    def test_concurrent_merchant_registration_has_one_pending_record(self):
        payload = {
            "business_name": "Concurrent Shop",
            "owner_name": "Owner",
            "phone": "0833333333",
            "email": "owner@example.com",
            "address": "Bangkok Thailand",
            "category": "restaurant",
        }
        results = self.concurrent(
            lambda: self.request("/api/merchants/register", "POST", payload)
        )
        self.assertEqual(sorted(status for status, _ in results), [201, 400])
        with app.db() as connection:
            applications = connection.execute(
                """SELECT COUNT(*) FROM merchant_applications
                   WHERE phone='0833333333' AND status='pending'"""
            ).fetchone()[0]
        self.assertEqual(applications, 1)

    def test_rider_with_active_delivery_cannot_be_deactivated(self):
        now = app.utcnow()
        with app.db() as connection:
            connection.execute(
                "INSERT INTO customers VALUES (?,?,?,?,?)",
                ("0844444444", "Customer", 0, now, now),
            )
            connection.execute(
                "INSERT INTO orders VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (
                    "MPP-RIDER-ACTIVE",
                    now,
                    "confirmed",
                    "Customer",
                    "0844444444",
                    "2026-07-29",
                    "delivery",
                    100,
                    "",
                    "cash",
                    "pending",
                ),
            )
            connection.execute(
                "INSERT INTO riders VALUES (?,?,?,?,?,?,?)",
                ("RDR-ACTIVE", "Active Rider", "0855555555", 1, 1, now, now),
            )
            connection.execute(
                """INSERT INTO deliveries(
                     order_id,zone_id,recipient_name,recipient_phone,address,
                     rider_id,status,tracking_code,assigned_at,updated_at
                   ) VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (
                    "MPP-RIDER-ACTIVE",
                    "central",
                    "Customer",
                    "0844444444",
                    "Bangkok",
                    "RDR-ACTIVE",
                    "assigned",
                    "TRK-RIDER-ACTIVE",
                    now,
                    now,
                ),
            )

        endpoint = "/api/admin/riders/RDR-ACTIVE"
        status, _ = self.request(
            endpoint, "PATCH", {"active": False}, admin=True
        )
        self.assertEqual(status, 400)
        with app.db() as connection:
            rider = connection.execute(
                "SELECT active,available FROM riders WHERE id='RDR-ACTIVE'"
            ).fetchone()
            connection.execute(
                """UPDATE deliveries SET status='cancelled'
                   WHERE order_id='MPP-RIDER-ACTIVE'"""
            )
        self.assertEqual(dict(rider), {"active": 1, "available": 1})

        status, result = self.request(
            endpoint, "PATCH", {"active": False}, admin=True
        )
        self.assertEqual(status, 200)
        self.assertEqual(result["rider"]["active"], 0)
        self.assertEqual(result["rider"]["available"], 0)


if __name__ == "__main__":
    unittest.main()
