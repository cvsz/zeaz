import json
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import app


class OperationalMutationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        root = Path(self.tmp.name)
        app.DATA, app.DB_PATH = root / "data", root / "data" / "operations.sqlite3"
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

    def request(self, path, method, payload):
        request = Request(
            self.base + path,
            data=json.dumps(payload, separators=(",", ":")).encode(),
            method=method,
            headers={
                "Content-Type": "application/json",
                "X-Admin-Key": "test-admin",
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

    def seed_inventory(self, item_id="INV-OPERATIONS", on_hand=10):
        now = app.utcnow()
        with app.db() as connection:
            connection.execute(
                "INSERT INTO inventory_items VALUES (?,?,?,?,?,?,?,?)",
                (item_id, "Operations Stock", "kg", on_hand, 2, 1, now, now),
            )

    def test_inventory_numbers_must_be_finite(self):
        for value in (float("nan"), float("inf"), float("-inf")):
            status, _ = self.request(
                "/api/admin/inventory",
                "POST",
                {
                    "name": "Invalid Stock",
                    "unit": "kg",
                    "on_hand": value,
                    "reorder_level": 1,
                },
            )
            self.assertEqual(status, 400)
        with app.db() as connection:
            self.assertEqual(
                connection.execute(
                    "SELECT COUNT(*) FROM inventory_items WHERE name='Invalid Stock'"
                ).fetchone()[0],
                0,
            )

    def test_adjustment_is_finite_and_requires_a_reason(self):
        self.seed_inventory()
        for delta, reason in (
            (float("nan"), "count"),
            (float("inf"), "count"),
            (1, ""),
        ):
            status, _ = self.request(
                "/api/admin/inventory/adjust",
                "POST",
                {
                    "inventory_item_id": "INV-OPERATIONS",
                    "delta": delta,
                    "reason": reason,
                },
            )
            self.assertEqual(status, 400)
        with app.db() as connection:
            item = connection.execute(
                "SELECT on_hand FROM inventory_items WHERE id='INV-OPERATIONS'"
            ).fetchone()
            movements = connection.execute(
                "SELECT COUNT(*) FROM inventory_movements"
            ).fetchone()[0]
            audits = connection.execute(
                """SELECT COUNT(*) FROM audit_logs
                   WHERE entity_id='INV-OPERATIONS' AND action='adjust'"""
            ).fetchone()[0]
        self.assertEqual(item["on_hand"], 10)
        self.assertEqual(movements, 0)
        self.assertEqual(audits, 0)

    def test_concurrent_adjustments_preserve_both_deltas(self):
        self.seed_inventory(on_hand=0)
        barrier = threading.Barrier(2)

        def adjust(_):
            barrier.wait(timeout=3)
            return self.request(
                "/api/admin/inventory/adjust",
                "POST",
                {
                    "inventory_item_id": "INV-OPERATIONS",
                    "delta": 1,
                    "reason": "cycle_count",
                },
            )

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(adjust, range(2)))
        self.assertEqual([status for status, _ in results], [200, 200])
        with app.db() as connection:
            item = connection.execute(
                "SELECT on_hand FROM inventory_items WHERE id='INV-OPERATIONS'"
            ).fetchone()
            movements = connection.execute(
                """SELECT COUNT(*) FROM inventory_movements
                   WHERE inventory_item_id='INV-OPERATIONS'"""
            ).fetchone()[0]
        self.assertEqual(item["on_hand"], 2)
        self.assertEqual(movements, 2)

    def test_recipe_quantity_must_be_finite(self):
        self.seed_inventory()
        for quantity in (float("nan"), float("inf"), float("-inf")):
            status, _ = self.request(
                "/api/admin/inventory/recipes",
                "POST",
                {
                    "menu_item_id": "classic",
                    "inventory_item_id": "INV-OPERATIONS",
                    "quantity": quantity,
                },
            )
            self.assertEqual(status, 400)
        with app.db() as connection:
            recipes = connection.execute(
                """SELECT COUNT(*) FROM menu_recipes
                   WHERE inventory_item_id='INV-OPERATIONS'"""
            ).fetchone()[0]
        self.assertEqual(recipes, 0)

    def test_settings_reject_noop_and_roll_back_partial_update(self):
        for payload in ({}, {"unknown": 1}):
            status, _ = self.request(
                "/api/admin/settings", "PATCH", payload
            )
            self.assertEqual(status, 400)

        status, _ = self.request(
            "/api/admin/settings",
            "PATCH",
            {"slot_capacity": 100, "advance_days": 0},
        )
        self.assertEqual(status, 400)
        with app.db() as connection:
            settings = app.config(connection)
            audits = connection.execute(
                """SELECT COUNT(*) FROM audit_logs
                   WHERE entity_type='settings' AND action='update'"""
            ).fetchone()[0]
        self.assertEqual(settings["slot_capacity"], app.DEFAULT_SETTINGS["slot_capacity"])
        self.assertEqual(audits, 0)

    def test_settings_audit_identifies_changed_keys(self):
        status, result = self.request(
            "/api/admin/settings",
            "PATCH",
            {"slot_capacity": 120, "advance_days": 30},
        )
        self.assertEqual(status, 200)
        self.assertEqual(result["settings"]["slot_capacity"], 120)
        with app.db() as connection:
            event = connection.execute(
                """SELECT details FROM audit_logs
                   WHERE entity_type='settings' AND action='update'
                   ORDER BY id DESC LIMIT 1"""
            ).fetchone()
        self.assertEqual(
            json.loads(event["details"]),
            {"keys": ["slot_capacity", "advance_days"]},
        )

    def test_delivery_pricing_numbers_must_be_finite(self):
        status, _ = self.request(
            "/api/admin/delivery-pricing",
            "POST",
            {
                "mode": "distance",
                "base_fee": 50,
                "per_km_fee": float("inf"),
                "maximum_km": 10,
                "store_latitude": 13.7563,
                "store_longitude": 100.5018,
            },
        )
        self.assertEqual(status, 400)
        with app.db() as connection:
            pricing = app.config(connection)["delivery_pricing"]
            audits = connection.execute(
                """SELECT COUNT(*) FROM audit_logs
                   WHERE entity_type='delivery_pricing' AND action='update'"""
            ).fetchone()[0]
        self.assertEqual(pricing, app.DEFAULT_SETTINGS["delivery_pricing"])
        self.assertEqual(audits, 0)

    def test_delivery_zone_rejects_fractional_and_boolean_money(self):
        for payload in (
            {"name": "Fractional Fee", "fee": 10.5, "minimum_order": 0},
            {"name": "Boolean Fee", "fee": True, "minimum_order": 0},
            {"name": "Fractional Minimum", "fee": 10, "minimum_order": 20.5},
            {"name": "Unknown Field", "fee": 10, "unknown": True},
            {"name": {"unexpected": "object"}, "fee": 10},
        ):
            status, _ = self.request("/api/admin/delivery-zones", "POST", payload)
            self.assertEqual(status, 400)
        with app.db() as connection:
            zones = connection.execute(
                """SELECT COUNT(*) FROM delivery_zones
                   WHERE id<>'central'"""
            ).fetchone()[0]
            audits = connection.execute(
                """SELECT COUNT(*) FROM audit_logs
                   WHERE entity_type='delivery_zone'"""
            ).fetchone()[0]
        self.assertEqual(zones, 0)
        self.assertEqual(audits, 0)

    def test_concurrent_delivery_zone_names_are_unique_case_insensitively(self):
        barrier = threading.Barrier(2)

        def create(name):
            barrier.wait(timeout=3)
            return self.request(
                "/api/admin/delivery-zones",
                "POST",
                {"name": name, "fee": 40, "minimum_order": 100},
            )

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(create, ("Bangkok East", "bangkok east")))
        self.assertEqual(sorted(status for status, _ in results), [201, 400])
        with app.db() as connection:
            zones = connection.execute(
                """SELECT name,fee,minimum_order FROM delivery_zones
                   WHERE id<>'central'"""
            ).fetchall()
            audits = connection.execute(
                """SELECT COUNT(*) FROM audit_logs
                   WHERE entity_type='delivery_zone' AND action='create'"""
            ).fetchone()[0]
        self.assertEqual(len(zones), 1)
        self.assertEqual(zones[0]["name"].casefold(), "bangkok east")
        self.assertEqual(zones[0]["fee"], 40)
        self.assertEqual(zones[0]["minimum_order"], 100)
        self.assertEqual(audits, 1)

    def test_business_profile_requires_exact_text_and_tax_identifier(self):
        original = app.DEFAULT_SETTINGS["business_profile"]
        invalid_profiles = (
            {
                "legal_name": "MooPiew",
                "tax_id": "12345678901234",
                "address": "Bangkok",
                "vat_registered": True,
            },
            {
                "legal_name": "MooPiew",
                "tax_id": "123-456-789-0123",
                "address": "Bangkok",
                "vat_registered": True,
            },
            {
                "legal_name": {"unexpected": "object"},
                "tax_id": "",
                "address": "Bangkok",
                "vat_registered": False,
            },
            {
                "legal_name": "MooPiew",
                "tax_id": "",
                "address": "Bangkok",
                "vat_registered": True,
            },
            {
                "legal_name": "MooPiew",
                "tax_id": "",
                "address": "Bangkok",
                "vat_registered": False,
                "unknown": True,
            },
        )
        for payload in invalid_profiles:
            status, _ = self.request(
                "/api/admin/business-profile", "POST", payload
            )
            self.assertEqual(status, 400)
        with app.db() as connection:
            profile = app.config(connection)["business_profile"]
            audits = connection.execute(
                """SELECT COUNT(*) FROM audit_logs
                   WHERE entity_type='business_profile'"""
            ).fetchone()[0]
        self.assertEqual(profile, original)
        self.assertEqual(audits, 0)

    def test_business_profile_is_canonical_and_audit_excludes_tax_data(self):
        status, result = self.request(
            "/api/admin/business-profile",
            "POST",
            {
                "legal_name": "  MooPiew   Company  ",
                "tax_id": "1234567890123",
                "address": "  Bangkok, Thailand  ",
                "branch": "  Head   Office  ",
                "vat_registered": True,
            },
        )
        self.assertEqual(status, 200)
        self.assertEqual(
            result["business_profile"],
            {
                "legal_name": "MooPiew Company",
                "tax_id": "1234567890123",
                "address": "Bangkok, Thailand",
                "branch": "Head Office",
                "vat_registered": True,
                "vat_rate": 7,
            },
        )
        with app.db() as connection:
            event = connection.execute(
                """SELECT details FROM audit_logs
                   WHERE entity_type='business_profile'
                   ORDER BY id DESC LIMIT 1"""
            ).fetchone()
        details = json.loads(event["details"])
        self.assertEqual(details["vat_registered"], True)
        self.assertEqual(
            details["fields"],
            ["legal_name", "tax_id", "address", "branch", "vat_registered"],
        )
        self.assertNotIn("1234567890123", event["details"])


if __name__ == "__main__":
    unittest.main()
