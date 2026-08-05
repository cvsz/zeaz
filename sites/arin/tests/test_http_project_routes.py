import json
import tempfile
import threading
import unittest
from http.client import HTTPConnection
from pathlib import Path

from arin_app import db
from arin_app.server import ArinHTTPServer
from arin_app.service import ArinService


class HttpProjectRouteTests(unittest.TestCase):
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
        response_headers = dict(response.getheaders())
        connection.close()
        if not raw:
            body = None
        elif "text/html" in response_headers.get("Content-Type", ""):
            body = raw.decode("utf-8")
        else:
            body = json.loads(raw.decode("utf-8"))
        return response.status, response_headers, body

    def test_authenticated_project_lifecycle_and_public_publish_boundary(self):
        self.request(
            "POST",
            "/api/auth/register",
            {"email": "builder@example.com", "name": "Builder", "password": "a sufficiently long password"},
        )
        _, headers, login = self.request(
            "POST",
            "/api/auth/login",
            {"email": "builder@example.com", "password": "a sufficiently long password"},
        )
        cookie = headers["Set-Cookie"].split(";", 1)[0]
        status, _, session = self.request("GET", "/api/auth/session", cookie=cookie)
        self.assertEqual(status, 200)
        csrf = session["csrf_token"]

        status, _, workspace_body = self.request(
            "POST",
            "/api/workspaces",
            {"name": "Builder Workspace"},
            cookie,
            csrf,
        )
        self.assertEqual(status, 201)
        workspace_id = workspace_body["workspace"]["id"]

        status, _, project_body = self.request(
            "POST",
            "/api/projects",
            {
                "workspace_id": workspace_id,
                "prompt": "Build a CRM for our sales team",
                "category": "internal",
            },
            cookie,
            csrf,
        )
        self.assertEqual(status, 201)
        project_id = project_body["project"]["id"]
        self.assertEqual(len(project_body["project"]["files"]), 3)

        status, _, _ = self.request(
            "PUT",
            f"/api/projects/{project_id}/files/index.html",
            {"content": "<!doctype html><title>Live edited app</title>"},
            cookie,
            csrf,
        )
        self.assertEqual(status, 200)

        status, preview_headers, preview_body = self.request(
            "GET", f"/preview/{project_id}", cookie=cookie
        )
        self.assertEqual(status, 200)
        self.assertIn("Live edited app", preview_body)
        self.assertIn("sandbox", preview_headers["Content-Security-Policy"])

        status, _, deployment_body = self.request(
            "POST", f"/api/projects/{project_id}/publish", {}, cookie, csrf
        )
        self.assertEqual(status, 200)
        slug = deployment_body["deployment"]["slug"]

        status, public_headers, public_body = self.request("GET", f"/app/{slug}")
        self.assertEqual(status, 200)
        self.assertIn("Live edited app", public_body)
        self.assertIn("sandbox", public_headers["Content-Security-Policy"])

        status, _, _ = self.request(
            "POST", f"/api/projects/{project_id}/unpublish", {}, cookie, csrf
        )
        self.assertEqual(status, 204)
        status, _, error = self.request("GET", f"/app/{slug}")
        self.assertEqual(status, 404)
        self.assertEqual(error["error"]["code"], "not_found")

    def test_project_creation_requires_authentication(self):
        status, _, error = self.request(
            "POST",
            "/api/projects",
            {"workspace_id": "wsp_missing", "prompt": "Build a CRM", "category": "internal"},
        )
        self.assertEqual(status, 401)
        self.assertEqual(error["error"]["code"], "unauthenticated")


if __name__ == "__main__":
    unittest.main()
