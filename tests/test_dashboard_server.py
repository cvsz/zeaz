import json
import os
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import urlopen

from dashboard.api.health import _positive_int as health_positive_int
from dashboard.api.server import DashboardHandler, _positive_int


class DashboardServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), DashboardHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.origin = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def test_health_endpoint_returns_snapshot_and_security_headers(self):
        with urlopen(f"{self.origin}/api/health", timeout=3) as response:
            payload = json.load(response)
            headers = response.headers
        self.assertEqual(payload["schemaVersion"], 1)
        self.assertIn("productionReadiness", payload["scores"])
        self.assertEqual(headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(headers["Referrer-Policy"], "no-referrer")
        self.assertIn("default-src 'self'", headers["Content-Security-Policy"])
        self.assertEqual(headers["Cache-Control"], "no-store")

    def test_index_is_served_and_missing_path_is_404(self):
        with urlopen(f"{self.origin}/", timeout=3) as response:
            body = response.read().decode()
        self.assertIn("Engineering Health", body)
        with self.assertRaises(HTTPError) as error:
            urlopen(f"{self.origin}/not-present", timeout=3)
        self.assertEqual(error.exception.code, 404)
        error.exception.close()

    def test_invalid_numeric_environment_uses_safe_defaults(self):
        with patch.dict(os.environ, {"DASHBOARD_REFRESH_SECONDS": "invalid"}):
            self.assertEqual(_positive_int("DASHBOARD_REFRESH_SECONDS", 10, 2), 10)
        with patch.dict(os.environ, {"DASHBOARD_EVIDENCE_TTL_HOURS": "invalid"}):
            self.assertEqual(
                health_positive_int("DASHBOARD_EVIDENCE_TTL_HOURS", 24), 24
            )

    def test_client_source_never_inserts_untrusted_html(self):
        source = (
            Path(__file__).resolve().parents[1] / "dashboard/assets/app.js"
        ).read_text(encoding="utf-8")
        self.assertNotIn("innerHTML", source)
        self.assertNotIn("insertAdjacentHTML", source)
        self.assertIn("textContent", source)


if __name__ == "__main__":
    unittest.main()
