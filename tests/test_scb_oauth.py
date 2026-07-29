import base64
import hashlib
import json
import os
import threading
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

from cryptography.fernet import Fernet

import app


class FakeResponse:
    headers = {}

    def __init__(self, payload):
        self.payload = json.dumps(payload).encode()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def read(self, _limit):
        return self.payload


class ScbOauthTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        root = Path(self.tmp.name)
        app.DATA, app.DB_PATH = root / "data", root / "data" / "oauth.sqlite3"
        app.initialise_database()
        self.key = Fernet.generate_key().decode()
        self.environment = {
            "SCB_AUTHORIZE_ENDPOINT": "https://sandbox.example/oauth/authorize",
            "SCB_OAUTH_TOKEN_ENDPOINT": "https://sandbox.example/oauth/token",
            "SCB_API_KEY": "application-key",
            "SCB_API_SECRET": "application-secret",
            "SCB_TOKEN_ENCRYPTION_KEY": self.key,
            "SCB_OAUTH_PKCE_ENABLED": "true",
            "SCB_OAUTH_PKCE_TOKEN_FIELD": "codeVerifier",
        }

    def tearDown(self):
        self.tmp.cleanup()

    def test_authorization_url_uses_s256_and_encrypts_verifier(self):
        response = FakeResponse(
            {"data": {"callbackUrl": "https://consent.example/start?existing=1"}}
        )
        with patch.dict(os.environ, self.environment, clear=False), patch.object(
            app, "scb_urlopen", return_value=response
        ):
            authorization_url = app.scb_authorize()
        query = parse_qs(urlparse(authorization_url).query)
        self.assertEqual(query["code_challenge_method"], ["S256"])
        self.assertEqual(query["existing"], ["1"])
        state = query["state"][0]
        with app.db() as connection:
            row = connection.execute(
                "SELECT verifier_cipher FROM oauth_states WHERE state=?", (state,)
            ).fetchone()
        self.assertNotIn("code_challenge", row["verifier_cipher"])
        verifier = Fernet(self.key.encode()).decrypt(
            row["verifier_cipher"].encode()
        ).decode()
        expected = (
            base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest())
            .decode()
            .rstrip("=")
        )
        self.assertEqual(query["code_challenge"], [expected])
        self.assertGreaterEqual(len(verifier), 43)
        self.assertLessEqual(len(verifier), 128)

    def test_authorization_rejects_non_https_provider_callback(self):
        response = FakeResponse(
            {"data": {"callbackUrl": "http://consent.example/start"}}
        )
        with patch.dict(os.environ, self.environment, clear=False), patch.object(
            app, "scb_urlopen", return_value=response
        ):
            with self.assertRaises(ValueError):
                app.scb_authorize()

    def test_exchange_sends_verifier_only_in_allowlisted_field(self):
        result = (
            {
                "data": {
                    "accessToken": "access",
                    "refreshToken": "refresh",
                    "expiresIn": 900,
                }
            },
            {"resourceownerid": "owner"},
        )
        with patch.dict(os.environ, self.environment, clear=False), patch.object(
            app, "scb_http", return_value=result
        ) as request, patch.object(app, "scb_store_token") as store:
            app.scb_exchange_auth_code("auth-code", "verifier")
        payload = request.call_args.args[1]
        self.assertEqual(payload["codeVerifier"], "verifier")
        self.assertNotIn("code_verifier", payload)
        store.assert_called_once()

        invalid = {**self.environment, "SCB_OAUTH_PKCE_TOKEN_FIELD": "unsafe"}
        with patch.dict(os.environ, invalid, clear=False):
            with self.assertRaises(ValueError):
                app.scb_exchange_auth_code("auth-code", "verifier")

    def test_state_is_consumed_exactly_once_under_concurrency(self):
        state = "s" * 40
        verifier = "v" * 64
        encrypted = Fernet(self.key.encode()).encrypt(verifier.encode()).decode()
        with app.db() as connection:
            connection.execute(
                """INSERT INTO oauth_states(state,expires_at,verifier_cipher)
                VALUES (?,?,?)""",
                (
                    state,
                    (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat(),
                    encrypted,
                ),
            )
        barrier = threading.Barrier(2)
        results = []

        def consume():
            barrier.wait()
            results.append(app.scb_consume_oauth_state(state))

        threads = [threading.Thread(target=consume) for _ in range(2)]
        with patch.dict(os.environ, self.environment, clear=False):
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()
        self.assertCountEqual(results, [verifier, None])
        self.assertIsNone(app.scb_consume_oauth_state(state))

    def test_expired_state_is_rejected(self):
        state = "e" * 40
        with app.db() as connection:
            connection.execute(
                """INSERT INTO oauth_states(state,expires_at,verifier_cipher)
                VALUES (?,'2000-01-01T00:00:00+00:00','')""",
                (state,),
            )
        self.assertIsNone(app.scb_consume_oauth_state(state))


if __name__ == "__main__":
    unittest.main()
