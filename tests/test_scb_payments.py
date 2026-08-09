import hashlib
import hmac
import json
import os
import threading
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from unittest.mock import patch

import app


class ScbPaymentLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        root = Path(self.tmp.name)
        app.DATA, app.DB_PATH = root / "data", root / "data" / "test.sqlite3"
        app.ADMIN_KEY = "test-admin"
        self.previous_scb_enabled = app.SCB_ENABLED
        app.SCB_ENABLED = True
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
        app.SCB_ENABLED = self.previous_scb_enabled
        self.tmp.cleanup()

    def seed_payment(self, order_status="new", payment_status="pending"):
        now = app.utcnow()
        with app.db() as connection:
            connection.execute(
                "INSERT INTO orders VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (
                    "MPP-PAYMENT",
                    now,
                    order_status,
                    "Payment Test",
                    "0812345678",
                    "2026-07-29",
                    "09:00–10:00",
                    100,
                    "",
                    "scb_qr",
                    payment_status,
                ),
            )
            connection.execute(
                """INSERT INTO payment_attempts VALUES
                   (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    "PAY-SCB-TEST",
                    "MPP-PAYMENT",
                    "scb_maemanee",
                    "MPP-PAYMENT-REF",
                    "SCB-ORDER-1",
                    100,
                    "pending",
                    "qr",
                    "T30",
                    "2099-01-01T00:00:00+00:00",
                    now,
                    now,
                    "",
                    "{}",
                ),
            )

    def request(self, path, payload, headers=None):
        raw = json.dumps(payload, separators=(",", ":")).encode()
        request = Request(
            self.base + path,
            data=raw,
            method="POST",
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

    def callback(self, inquiry_result, signature="valid"):
        payload = {"data": {"orderId": "SCB-ORDER-1"}}
        raw = json.dumps(payload, separators=(",", ":")).encode()
        secret = "webhook-secret"
        digest = hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()
        supplied = digest if signature == "valid" else "invalid"
        with patch.dict(
            os.environ, {"SCB_WEBHOOK_SECRET": secret}, clear=False
        ), patch.object(
            app, "scb_inquire_payment", return_value=inquiry_result
        ) as inquiry:
            status, result = self.request(
                "/api/scb/payment/confirm",
                payload,
                {"X-SCB-Signature": f"sha256={supplied}"},
            )
        return status, result, inquiry

    def payment_state(self):
        with app.db() as connection:
            payment = dict(
                connection.execute(
                    "SELECT * FROM payment_attempts WHERE id='PAY-SCB-TEST'"
                ).fetchone()
            )
            order = dict(
                connection.execute(
                    "SELECT status,payment_status FROM orders WHERE id='MPP-PAYMENT'"
                ).fetchone()
            )
            audits = [
                dict(row)
                for row in connection.execute(
                    """SELECT action,details FROM audit_logs
                       WHERE entity_id='PAY-SCB-TEST' ORDER BY id"""
                )
            ]
        return payment, order, audits

    def test_verified_callback_marks_active_order_paid(self):
        self.seed_payment()
        status, result, inquiry = self.callback(
            ({"data": {"paymentStatus": "PAID"}}, True)
        )
        self.assertEqual(status, 200)
        self.assertEqual(result["status"], "paid")
        inquiry.assert_called_once()
        payment, order, audits = self.payment_state()
        self.assertEqual(payment["status"], "paid")
        self.assertTrue(payment["confirmed_at"])
        self.assertEqual(order["payment_status"], "paid")
        self.assertEqual(audits[-1]["action"], "payment_confirmed")
        details = json.loads(audits[-1]["details"])
        self.assertEqual(details["provider_order_id"], "SCB-ORDER-1")
        self.assertTrue(details["signature_verified"])

    def test_verified_callback_records_cancelled_order_for_reconciliation(self):
        self.seed_payment(order_status="cancelled")
        status, result, _ = self.callback(
            ({"data": {"transactionStatus": "SUCCESS"}}, True)
        )
        self.assertEqual(status, 200)
        self.assertEqual(result["status"], "paid")
        payment, order, audits = self.payment_state()
        self.assertEqual(payment["status"], "paid")
        self.assertEqual(order, {"status": "cancelled", "payment_status": "pending"})
        self.assertEqual(
            audits[-1]["action"], "payment_received_cancelled_order"
        )
        details = json.loads(audits[-1]["details"])
        self.assertTrue(details["requires_reconciliation"])
        self.assertEqual(details["provider_order_id"], "SCB-ORDER-1")
        self.assertTrue(details["signature_verified"])

    def test_invalid_signature_never_calls_provider_inquiry(self):
        self.seed_payment()
        status, _, inquiry = self.callback(
            ({"data": {"paymentStatus": "PAID"}}, True),
            signature="invalid",
        )
        self.assertEqual(status, 401)
        inquiry.assert_not_called()
        payment, order, audits = self.payment_state()
        self.assertEqual(payment["status"], "pending")
        self.assertEqual(order["payment_status"], "pending")
        self.assertEqual(audits, [])

    def test_pending_callback_preserves_pending_state_and_provider_response(self):
        self.seed_payment()
        response = {"data": {"paymentStatus": "PENDING"}}
        status, result, _ = self.callback((response, False))
        self.assertEqual(status, 200)
        self.assertEqual(result["status"], "pending")
        payment, order, audits = self.payment_state()
        self.assertEqual(payment["status"], "pending")
        self.assertEqual(json.loads(payment["provider_response"]), response)
        self.assertEqual(order["payment_status"], "pending")
        self.assertEqual(audits[-1]["action"], "payment_callback_pending")

    def test_admin_inquiry_is_idempotent_after_paid_callback(self):
        self.seed_payment()
        self.callback(({"data": {"paymentStatus": "PAID"}}, True))
        with patch.object(
            app, "scb_inquire_payment", side_effect=AssertionError("must not call")
        ):
            status, result = self.request(
                "/api/admin/payments/scb/PAY-SCB-TEST/inquire",
                {},
                {"X-Admin-Key": "test-admin"},
            )
        self.assertEqual(status, 200)
        self.assertEqual(result["inquiry"], "already_paid")

    def test_callback_rejects_missing_and_unknown_provider_order(self):
        secret = "webhook-secret"
        for payload, expected_status in (
            ({"data": {}}, 400),
            ({"data": {"orderId": "UNKNOWN"}}, 404),
        ):
            raw = json.dumps(payload, separators=(",", ":")).encode()
            digest = hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()
            with self.subTest(payload=payload), patch.dict(
                os.environ, {"SCB_WEBHOOK_SECRET": secret}, clear=False
            ):
                status, _ = self.request(
                    "/api/scb/payment/confirm",
                    payload,
                    {"X-SCB-Signature": f"sha256={digest}"},
                )
            self.assertEqual(status, expected_status)

    def test_callback_provider_failure_preserves_payment_state(self):
        self.seed_payment()
        status, result, inquiry = self.callback(
            ({"data": {"paymentStatus": "PAID"}}, True)
        )
        self.assertEqual(status, 200)
        self.assertEqual(result["status"], "paid")
        inquiry.assert_called_once()

        with app.db() as connection:
            connection.execute(
                """UPDATE payment_attempts
                   SET status='pending',confirmed_at='',provider_response='{}'
                   WHERE id='PAY-SCB-TEST'"""
            )
            connection.execute(
                """UPDATE orders SET payment_status='pending'
                   WHERE id='MPP-PAYMENT'"""
            )
        payload = {"data": {"orderId": "SCB-ORDER-1"}}
        raw = json.dumps(payload, separators=(",", ":")).encode()
        secret = "webhook-secret"
        digest = hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()
        with patch.dict(
            os.environ, {"SCB_WEBHOOK_SECRET": secret}, clear=False
        ), patch.object(
            app, "scb_inquire_payment", side_effect=ValueError("provider unavailable")
        ):
            status, result = self.request(
                "/api/scb/payment/confirm",
                payload,
                {"X-SCB-Signature": f"sha256={digest}"},
            )
        self.assertEqual(status, 503)
        self.assertEqual(result["error"], "provider unavailable")
        payment, order, _ = self.payment_state()
        self.assertEqual(payment["status"], "pending")
        self.assertEqual(order["payment_status"], "pending")

    def test_admin_inquiry_rejects_employee_role(self):
        self.seed_payment()
        original_admin = app.ADMIN_KEY
        app.ADMIN_KEY = ""
        try:
            status, _ = self.request(
                "/api/admin/payments/scb/PAY-SCB-TEST/inquire",
                {},
                {"X-Employee-Key": "test-employee"},
            )
        finally:
            app.ADMIN_KEY = original_admin
        self.assertEqual(status, 401)

    def test_spending_limit_rejects_single_payment_above_cap(self):
        with patch.dict(
            os.environ,
            {
                "SCB_MAX_PAYMENT_THB": "100",
                "SCB_DAILY_PAYMENT_LIMIT_THB": "250",
            },
            clear=False,
        ), app.db() as connection:
            with self.assertRaisesRegex(ValueError, "single payment limit"):
                app.check_scb_spending_limit(connection, 101)

    def test_spending_limit_counts_open_and_paid_attempts_for_daily_cap(self):
        self.seed_payment()
        with patch.dict(
            os.environ,
            {
                "SCB_MAX_PAYMENT_THB": "250",
                "SCB_DAILY_PAYMENT_LIMIT_THB": "250",
            },
            clear=False,
        ), app.db() as connection:
            with self.assertRaisesRegex(ValueError, "daily payment limit"):
                app.check_scb_spending_limit(connection, 151)

    def test_spending_limit_allows_amount_when_daily_budget_remains(self):
        with patch.dict(
            os.environ,
            {
                "SCB_MAX_PAYMENT_THB": "250",
                "SCB_DAILY_PAYMENT_LIMIT_THB": "250",
            },
            clear=False,
        ), app.db() as connection:
            app.check_scb_spending_limit(connection, 250)


if __name__ == "__main__":
    unittest.main()
