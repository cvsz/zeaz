import http.client
import json
import os
import threading
import unittest
from datetime import datetime, timedelta, timezone
from tempfile import TemporaryDirectory
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

import app


class FakeTikTokResponse:
    headers = {}

    def __init__(self, payload):
        self.payload = json.dumps(payload).encode()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def read(self, _limit=-1):
        return self.payload


class ZttshopSiteTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        root = app.Path(self.tmp.name)
        app.DATA = root / "data"
        app.DB_PATH = root / "data" / "zttshop.sqlite3"
        app.initialise_database()

    def tearDown(self):
        self.tmp.cleanup()

    @classmethod
    def setUpClass(cls):
        cls.server = app.BoundedHTTPServer(("127.0.0.1", 0), app.Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.port = cls.server.server_port

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def request(self, path: str):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=3)
        conn.request("GET", path, headers={"Host": "zttshop.zeaz.dev"})
        response = conn.getresponse()
        body = response.read().decode("utf-8")
        conn.close()
        return response.status, body

    def request_with_headers(self, path: str):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=3)
        conn.request("GET", path, headers={"Host": "zttshop.zeaz.dev"})
        response = conn.getresponse()
        body = response.read().decode("utf-8")
        headers = dict(response.getheaders())
        conn.close()
        return response.status, body, headers

    def test_homepage_privacy_terms_and_callback_are_served(self):
        status, body = self.request("/")
        self.assertEqual(status, 200)
        self.assertIn("Preparing the TikTok sign-in flow", body)
        self.assertIn("loading", body.lower())
        self.assertIn("/assets/zttshop.css", body)

        status, body = self.request("/privacy")
        self.assertEqual(status, 200)
        self.assertIn("privacy policy", body.lower())
        self.assertIn("/assets/zttshop.css", body)

        status, body = self.request("/terms")
        self.assertEqual(status, 200)
        self.assertIn("terms of service", body.lower())
        self.assertIn("/assets/zttshop.css", body)

        status, body = self.request("/api/auth/tiktok/callback")
        self.assertEqual(status, 200)
        self.assertIn("TikTok authorization responses will land here", body)

    def test_tiktok_start_redirects_and_callback_exchanges_code(self):
        token_key = app.Fernet.generate_key().decode()
        with patch.object(app, "TIKTOK_CLIENT_KEY", "test-client-key"), patch.object(
            app, "TIKTOK_CLIENT_SECRET", "test-client-secret"
        ), patch.object(
            app, "TIKTOK_REDIRECT_URI", "https://zttshop.zeaz.dev/api/auth/tiktok/callback"
        ), patch.object(app, "TIKTOK_SCOPE", "user.info.basic"), patch.dict(
            os.environ, {"TIKTOK_TOKEN_ENCRYPTION_KEY": token_key}, clear=False
        ), patch.object(
            app,
            "urlopen",
            return_value=FakeTikTokResponse(
                {
                    "data": {
                        "access_token": "access-token",
                        "refresh_token": "refresh-token",
                        "open_id": "open-id-123",
                        "scope": "user.info.basic",
                        "token_type": "Bearer",
                        "expires_in": 86400,
                        "refresh_expires_in": 31536000,
                    }
                }
            ),
        ):
            status, _, headers = self.request_with_headers("/api/auth/tiktok/start")
            self.assertEqual(status, 302)
            location = headers["Location"]
            query = parse_qs(urlparse(location).query)
            state = query["state"][0]
            self.assertEqual(query["client_key"], ["test-client-key"])
            self.assertEqual(query["response_type"], ["code"])
            self.assertEqual(
                query["redirect_uri"],
                ["https://zttshop.zeaz.dev/api/auth/tiktok/callback"],
            )

            status, body = self.request(
                f"/api/auth/tiktok/callback?code=test-code&state={state}"
            )
            self.assertEqual(status, 200)
            self.assertIn("Authorization complete", body)
            self.assertIn("open-id-123", body)

        with app.db() as connection:
            row = connection.execute(
                "SELECT subject, owner_cipher, access_cipher, refresh_cipher FROM oauth_tokens WHERE subject=?",
                ("tiktok_zttshop",),
            ).fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row["subject"], "tiktok_zttshop")


if __name__ == "__main__":
    unittest.main()
