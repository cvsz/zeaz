import base64
import json
import subprocess
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from unittest.mock import patch

import app
from cryptography.fernet import Fernet


class DocumentApiTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        root = Path(self.tmp.name)
        app.DATA, app.DB_PATH = root / "data", root / "data" / "test.sqlite3"
        app.ADMIN_KEY = "test-admin"
        app.EMPLOYEE_KEY = "test-employee"
        app.KITCHEN_KEY = "test-kitchen"
        self.document_key = Fernet.generate_key().decode()
        self.environment = patch.dict(
            "os.environ", {"DOCUMENT_ENCRYPTION_KEY": self.document_key}
        )
        self.environment.start()
        app.initialise_database()
        self.server = app.BoundedHTTPServer(("127.0.0.1", 0), app.Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.environment.stop()
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

    def test_provider_specific_requirement_matrix(self):
        expected = {
            "grab": (6, 6, 0),
            "bolt": (8, 5, 3),
            "lineman": (0, 0, 0),
            "lalamove": (6, 6, 0),
        }
        for provider, (count, required, optional) in expected.items():
            with self.subTest(provider=provider):
                status, result = self.request(
                    f"/api/providers/{provider}/requirements/rider"
                )
                self.assertEqual(status, 200)
                self.assertEqual(len(result["requirements"]), count)
                self.assertEqual(
                    sum(item["is_required"] for item in result["requirements"]),
                    required,
                )
                self.assertEqual(
                    sum(item["is_optional"] for item in result["requirements"]),
                    optional,
                )
                for item in result["requirements"]:
                    self.assertEqual(item["provider_slug"], provider)
                    self.assertEqual(item["subject_type"], "rider")
                    self.assertEqual(item["country"], "TH")
                    self.assertIn("source", item["metadata"])

    def test_provider_specific_merchant_type_filtering(self):
        _, individual = self.request(
            "/api/providers/grab/requirements/merchant?merchant_type=individual"
        )
        _, company = self.request(
            "/api/providers/grab/requirements/merchant?merchant_type=company"
        )
        self.assertEqual(
            {item["document_slug"] for item in individual["requirements"]},
            {"national-id", "bank-account"},
        )
        self.assertEqual(
            {item["document_slug"] for item in company["requirements"]},
            {
                "company-certificate",
                "vat-certificate",
                "shareholder-list",
                "director-id",
                "business-bank-account",
            },
        )
        for provider in ("bolt", "lineman", "lalamove"):
            with self.subTest(provider=provider):
                _, result = self.request(
                    f"/api/providers/{provider}/requirements/merchant"
                )
                self.assertEqual(result["requirements"], [])

    def test_admin_versions_policy_and_rejects_historical_upload(self):
        status, version = self.request(
            "/api/admin/document-requirements/grab-rider-national-id",
            "PATCH",
            {
                "display_order": 9,
                "is_required": True,
                "is_optional": False,
                "metadata": {
                    "label_th": "บัตรประชาชนฉบับปัจจุบัน",
                    "reviewed_at": "2026-07-28",
                },
            },
        )
        self.assertEqual(status, 201)
        new_id = version["requirement_id"]

        _, public = self.request("/api/providers/grab/requirements/rider")
        ids = {item["id"] for item in public["requirements"]}
        self.assertNotIn("grab-rider-national-id", ids)
        self.assertIn(new_id, ids)
        current = next(item for item in public["requirements"] if item["id"] == new_id)
        self.assertEqual(current["display_order"], 9)
        self.assertEqual(
            current["metadata"]["label_th"], "บัตรประชาชนฉบับปัจจุบัน"
        )

        _, admin = self.request("/api/admin/document-requirements")
        versions = {
            item["id"]: item
            for item in admin["requirements"]
            if item["id"] in {"grab-rider-national-id", new_id}
        }
        self.assertFalse(versions["grab-rider-national-id"]["is_current"])
        self.assertTrue(versions[new_id]["is_current"])
        self.assertEqual(
            versions["grab-rider-national-id"]["effective_to"],
            versions[new_id]["effective_from"],
        )

        with self.assertRaises(HTTPError) as historical:
            self.request(
                "/api/admin/document-requirements/grab-rider-national-id",
                "PATCH",
                {"display_order": 1},
            )
        self.assertEqual(historical.exception.code, 400)
        historical.exception.close()

        png = base64.b64encode(b"\x89PNG\r\n\x1a\nvalid").decode()
        with self.assertRaises(HTTPError) as upload:
            self.request(
                "/api/documents/upload",
                "POST",
                {
                    "provider": "grab",
                    "subject_type": "rider",
                    "subject_id": "RDR-TEST",
                    "requirement_id": "grab-rider-national-id",
                    "filename": "id.png",
                    "mime_type": "image/png",
                    "content_base64": png,
                },
            )
        self.assertEqual(upload.exception.code, 400)
        upload.exception.close()

        with app.db() as connection:
            event = connection.execute(
                """SELECT action,entity_id,details FROM audit_logs
                   WHERE entity_type='provider_document_requirement'
                   ORDER BY id DESC LIMIT 1"""
            ).fetchone()
        self.assertEqual(event["action"], "version")
        self.assertEqual(event["entity_id"], new_id)
        self.assertEqual(
            json.loads(event["details"])["previous_id"],
            "grab-rider-national-id",
        )

    def test_concurrent_policy_versioning_has_one_successor(self):
        barrier = threading.Barrier(2)

        def version():
            barrier.wait(timeout=2)
            try:
                status, result = self.request(
                    "/api/admin/document-requirements/grab-rider-driver-license",
                    "PATCH",
                    {"display_order": 7},
                )
                return status, result
            except HTTPError as error:
                status = error.code
                result = json.loads(error.read())
                error.close()
                return status, result

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: version(), range(2)))

        self.assertEqual(sorted(status for status, _ in results), [201, 400])
        with app.db() as connection:
            current = connection.execute(
                """SELECT COUNT(*) FROM provider_document_requirements
                   WHERE provider_id='provider-grab'
                     AND document_type_id='document-type-driver-license'
                     AND subject_type='rider' AND effective_to=''"""
            ).fetchone()[0]
        self.assertEqual(current, 1)

    def test_upload_verify_and_history(self):
        png = base64.b64encode(b"\x89PNG\r\n\x1a\nvalid").decode()
        status, result = self.request("/api/documents/upload", "POST", {
            "provider": "grab", "subject_type": "rider", "subject_id": "RDR-TEST",
            "requirement_id": "grab-rider-national-id", "filename": "id.png",
            "mime_type": "image/png", "content_base64": png,
        })
        self.assertEqual(status, 201)
        document_id = result["document"]["id"]
        with app.db() as connection:
            stored = connection.execute(
                "SELECT storage_path,metadata FROM uploaded_documents WHERE id=?",
                (document_id,),
            ).fetchone()
        encrypted = Path(stored["storage_path"]).read_bytes()
        self.assertNotIn(b"valid", encrypted)
        self.assertEqual(Fernet(self.document_key.encode()).decrypt(encrypted), b"\x89PNG\r\n\x1a\nvalid")
        self.assertEqual(json.loads(stored["metadata"])["storage_encryption"], "fernet-v1")
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
        error.exception.close()

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
