import json
import tempfile
import threading
import unittest
from http.client import HTTPConnection
from pathlib import Path

from arin_app import db
from arin_app.server import ArinHTTPServer
from arin_app.service import ArinService


class HttpAuthRouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        connection = db.connect(Path(cls.tmp.name) / "arin.sqlite3")
        db.initialise(connection)
        cls.server = ArinHTTPServer(("127.0.0.1", 0), ArinService(connection))
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.port = cls.server.server_port

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)
        cls.tmp.cleanup()

    def request(self, method, path, payload=None, cookie="", csrf=""):
        connection = HTTPConnection("127.0.0.1", self.port, timeout=3)
        body = None if payload is None else json.dumps(payload).encode("utf-8")
        headers = {"Accept": "application/json"}
        if body is not None:
            headers["Content-Type"] = "application/json"
            headers["Content-Length"] = str(len(body))
        if cookie:
            headers["Cookie"] = cookie
        if csrf:
            headers["X-CSRF-Token"] = csrf
        connection.request(method, path, body=body, headers=headers)
        response = connection.getresponse()
        raw = response.read()
        headers = dict(response.getheaders())
        connection.close()
        payload = json.loads(raw.decode("utf-8")) if raw else None
        return response.status, headers, payload

    def test_register_login_session_and_logout_use_real_cookie_session(self):
        status, _, body = self.request(
            "POST",
            "/api/auth/register",
            {"email": "owner@example.com", "name": "Owner", "password": "a sufficiently long password"},
        )
        self.assertEqual(status, 201)
        self.assertEqual(body["user"]["email"], "owner@example.com")

        status, headers, body = self.request(
            "POST",
            "/api/auth/login",
            {"email": "owner@example.com", "password": "a sufficiently long password"},
        )
        self.assertEqual(status, 200)
        cookie = headers["Set-Cookie"].split(";", 1)[0]
        self.assertIn("arin_session=", cookie)
        self.assertIn("HttpOnly", headers["Set-Cookie"])
        self.assertIn("Secure", headers["Set-Cookie"])
        csrf = body["csrf_token"]

        status, _, session = self.request("GET", "/api/auth/session", cookie=cookie)
        self.assertEqual(status, 200)
        self.assertEqual(session["user"]["email"], "owner@example.com")
        rotated_csrf = session["csrf_token"]
        self.assertNotEqual(rotated_csrf, csrf)

        status, _, _ = self.request(
            "POST", "/api/auth/logout", cookie=cookie, csrf=rotated_csrf
        )
        self.assertEqual(status, 204)
        status, _, error = self.request("GET", "/api/auth/session", cookie=cookie)
        self.assertEqual(status, 401)
        self.assertEqual(error["error"]["code"], "unauthenticated")

    def test_state_changing_auth_route_rejects_bad_csrf_without_revoking_session(self):
        self.request(
            "POST",
            "/api/auth/register",
            {"email": "csrf@example.com", "name": "CSRF", "password": "a sufficiently long password"},
        )
        _, headers, body = self.request(
            "POST",
            "/api/auth/login",
            {"email": "csrf@example.com", "password": "a sufficiently long password"},
        )
        cookie = headers["Set-Cookie"].split(";", 1)[0]
        status, _, error = self.request(
            "POST", "/api/auth/logout", cookie=cookie, csrf="not-the-token"
        )
        self.assertEqual(status, 403)
        self.assertEqual(error["error"]["code"], "csrf_failed")

        status, _, session = self.request("GET", "/api/auth/session", cookie=cookie)
        self.assertEqual(status, 200)
        self.assertEqual(session["user"]["email"], "csrf@example.com")
        self.assertNotEqual(session["csrf_token"], body["csrf_token"])

    def test_health_is_public_and_malformed_json_has_stable_error(self):
        status, _, body = self.request("GET", "/api/health")
        self.assertEqual(status, 200)
        self.assertEqual(body["status"], "ok")

        connection = HTTPConnection("127.0.0.1", self.port, timeout=3)
        connection.request(
            "POST",
            "/api/auth/register",
            body=b"{not-json",
            headers={"Content-Type": "application/json", "Content-Length": "9"},
        )
        response = connection.getresponse()
        body = json.loads(response.read().decode("utf-8"))
        connection.close()
        self.assertEqual(response.status, 400)
        self.assertEqual(body["error"]["code"], "invalid_json")


if __name__ == "__main__":
    unittest.main()
