import base64
import json
import subprocess
import threading
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import app


class DocumentApiTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        root = Path(self.tmp.name)
        app.DATA, app.DB_PATH = root / "data", root / "data" / "test.sqlite3"
        app.ADMIN_KEY = "test-admin"
        app.EMPLOYEE_KEY = "test-employee"
        app.KITCHEN_KEY = "test-kitchen"
        app.initialise_database()
        self.server = app.BoundedHTTPServer(("127.0.0.1", 0), app.Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.tmp.cleanup()

    def request(self, path, method="GET", payload=None):
        body = json.dumps(payload).encode() if payload is not None else None
        request = Request(self.base + path, data=body, method=method, headers={"X-Admin-Key": "test-admin", "Content-Type": "application/json"})
        with urlopen(request, timeout=3) as response:
            return response.status, json.loads(response.read())

    def test_provider_requirements_are_data_driven(self):
        status, result = self.request("/api/providers/grab/requirements/rider")
        self.assertEqual(status, 200)
        self.assertEqual(result["requirements"][0]["document_slug"], "national-id")
        self.assertGreaterEqual(len(result["requirements"]), 5)

    def test_upload_verify_and_history(self):
        png = base64.b64encode(b"\x89PNG\r\n\x1a\nvalid").decode()
        status, result = self.request("/api/documents/upload", "POST", {
            "provider": "grab", "subject_type": "rider", "subject_id": "RDR-TEST",
            "requirement_id": "grab-rider-national-id", "filename": "id.png",
            "mime_type": "image/png", "content_base64": png,
        })
        self.assertEqual(status, 201)
        document_id = result["document"]["id"]
        status, result = self.request(f"/api/documents/{document_id}", "PATCH", {"status": "approved", "reason": "checked"})
        self.assertEqual(status, 200)
        self.assertEqual(result["document"]["status"], "approved")
        status, result = self.request("/api/documents/history?document_id=" + document_id)
        self.assertEqual(status, 200)
        self.assertEqual(len(result["history"]), 2)

    def test_upload_rejects_mismatched_mime(self):
        with self.assertRaises(HTTPError) as error:
            self.request("/api/documents/upload", "POST", {
                "provider": "grab", "subject_type": "rider", "subject_id": "RDR-TEST",
                "requirement_id": "grab-rider-national-id", "filename": "id.pdf",
                "mime_type": "application/pdf", "content_base64": base64.b64encode(b"not a pdf").decode(),
            })
        self.assertEqual(error.exception.code, 400)

    def test_frontend_document_renderer_contract(self):
        with urlopen(self.base + "/documents.html", timeout=3) as response:
            page = response.read().decode()
        self.assertIn("document-upload/document-page.js", page)
        source = Path(app.ROOT / "web/components/document-upload/document-upload.js").read_text(encoding="utf-8")
        self.assertIn("ondrop", source)
        self.assertIn("capture=\"environment\"", source)
        subprocess.run(["node", "--check", str(app.ROOT / "web/components/document-upload/document-upload.js")], check=True, capture_output=True)


if __name__ == "__main__":
    unittest.main()
