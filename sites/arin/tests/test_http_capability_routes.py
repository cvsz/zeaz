import base64
import json
import tempfile
import threading
import unittest
from http.client import HTTPConnection
from pathlib import Path

from cryptography.fernet import Fernet

from arin_app import db
from arin_app.server import ArinHTTPServer
from arin_app.service import ArinService


class HttpCapabilityRouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        root = Path(cls.tmp.name)
        connection = db.connect(root / "arin.sqlite3")
        db.initialise(connection)
        service = ArinService(
            connection,
            asset_root=root / "assets",
            connector_key=Fernet.generate_key(),
        )
        cls.server = ArinHTTPServer(("127.0.0.1", 0), service)
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
            parsed = None
        elif "application/json" in response_headers.get("Content-Type", ""):
            parsed = json.loads(raw.decode("utf-8"))
        else:
            parsed = raw
        return response.status, response_headers, parsed

    def auth(self, email, name):
        password = "a sufficiently long password"
        self.request(
            "POST",
            "/api/auth/register",
            {"email": email, "name": name, "password": password},
        )
        status, headers, _ = self.request(
            "POST", "/api/auth/login", {"email": email, "password": password}
        )
        self.assertEqual(status, 200)
        cookie = headers["Set-Cookie"].split(";", 1)[0]
        status, _, session = self.request("GET", "/api/auth/session", cookie=cookie)
        self.assertEqual(status, 200)
        return cookie, session["csrf_token"]

    def test_studio_capabilities_have_authenticated_and_public_boundaries(self):
        cookie, csrf = self.auth("capabilities@example.com", "Capabilities Owner")
        status, _, workspace_body = self.request(
            "POST", "/api/workspaces", {"name": "Capabilities Workspace"}, cookie, csrf
        )
        self.assertEqual(status, 201)
        workspace_id = workspace_body["workspace"]["id"]

        status, _, project_body = self.request(
            "POST",
            "/api/projects",
            {
                "workspace_id": workspace_id,
                "prompt": "Build a real customer operations dashboard",
                "category": "customer",
            },
            cookie,
            csrf,
        )
        self.assertEqual(status, 201)
        project_id = project_body["project"]["id"]

        status, _, projects = self.request(
            "GET", f"/api/projects?workspace_id={workspace_id}", cookie=cookie
        )
        self.assertEqual(status, 200)
        self.assertEqual(projects["projects"][0]["id"], project_id)

        status, _, settings = self.request(
            "PUT",
            f"/api/projects/{project_id}/settings",
            {"title": "Customer Ops", "primary_color": "#123456"},
            cookie,
            csrf,
        )
        self.assertEqual(status, 200)
        self.assertEqual(settings["settings"]["title"], "Customer Ops")

        asset_data = base64.b64encode(b"brand-image").decode("ascii")
        status, _, asset_body = self.request(
            "POST",
            f"/api/projects/{project_id}/assets",
            {"filename": "brand.png", "mime_type": "image/png", "data_base64": asset_data},
            cookie,
            csrf,
        )
        self.assertEqual(status, 201)
        asset_id = asset_body["asset"]["id"]
        status, _, assets = self.request(
            "GET", f"/api/projects/{project_id}/assets", cookie=cookie
        )
        self.assertEqual(status, 200)
        self.assertEqual(assets["assets"][0]["id"], asset_id)

        status, _, connector_body = self.request(
            "POST",
            f"/api/projects/{project_id}/connectors",
            {
                "kind": "webhook",
                "label": "Ops webhook",
                "config": {"url": "https://example.com", "secret": "private-value"},
            },
            cookie,
            csrf,
        )
        self.assertEqual(status, 201)
        self.assertNotIn("config", connector_body["connector"])
        status, _, connectors = self.request(
            "GET", f"/api/projects/{project_id}/connectors", cookie=cookie
        )
        self.assertEqual(status, 200)
        self.assertNotIn("private-value", json.dumps(connectors))

        status, _, message_body = self.request(
            "POST",
            f"/api/projects/{project_id}/messages",
            {"role": "user", "content": "Add a customer health score."},
            cookie,
            csrf,
        )
        self.assertEqual(status, 201)
        status, _, messages = self.request(
            "GET", f"/api/projects/{project_id}/messages", cookie=cookie
        )
        self.assertEqual(status, 200)
        self.assertEqual(messages["messages"][0]["id"], message_body["message"]["id"])

        status, _, invite_body = self.request(
            "POST",
            f"/api/workspaces/{workspace_id}/invites",
            {"email": "invitee@example.com", "role": "viewer"},
            cookie,
            csrf,
        )
        self.assertEqual(status, 201)
        self.assertTrue(invite_body["invite"]["token"])
        status, _, invites = self.request(
            "GET", f"/api/workspaces/{workspace_id}/invites", cookie=cookie
        )
        self.assertEqual(status, 200)
        self.assertNotIn("token", invites["invites"][0])

        status, _, _ = self.request(
            "POST", f"/api/projects/{project_id}/publish", {}, cookie, csrf
        )
        self.assertEqual(status, 200)
        status, public_headers, public_asset = self.request(
            "GET", f"/api/public-assets/{asset_id}"
        )
        self.assertEqual(status, 200)
        self.assertEqual(public_headers["Content-Type"], "image/png")
        self.assertEqual(public_asset, b"brand-image")


if __name__ == "__main__":
    unittest.main()
