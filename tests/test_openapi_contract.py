import ast
import json
import re
import threading
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import yaml

import app


OPENAPI = Path(__file__).resolve().parents[1] / "docs" / "openapi.yaml"
HTTP_METHODS = {"get", "post", "put", "patch", "delete", "head", "options"}
HANDLER_METHODS = {
    "do_GET": "get",
    "do_POST": "post",
    "_do_PATCH": "patch",
    "do_DELETE": "delete",
}
RUNTIME_PATTERN_TEMPLATES = {
    r"(?:/api)?/providers/([a-z0-9-]+)": {
        "/api/providers/{provider}",
    },
    r"(?:/api)?/providers/([a-z0-9-]+)/requirements(?:/(rider|merchant))?": {
        "/api/providers/{provider}/requirements",
        "/api/providers/{provider}/requirements/{subject}",
    },
    r"/api/tracking/(TRK-[A-F0-9]{32})/events": {
        "/api/tracking/{trackingCode}/events",
    },
    r"/api/tracking/(TRK-[A-F0-9]{32})": {
        "/api/tracking/{trackingCode}",
    },
    r"/api/admin/receipts/(RCT-[A-Z0-9-]+)/print": {
        "/api/admin/receipts/{receiptId}/print",
    },
    r"/api/orders/(MPP-[A-Z0-9-]+)/payments/scb/qr": {
        "/api/orders/{orderId}/payments/scb/qr",
    },
    r"/api/admin/orders/(MPP-[A-Z0-9-]+)/receipt": {
        "/api/admin/orders/{orderId}/receipt",
    },
    r"/api/admin/receipts/(RCT-[A-Z0-9-]+)/tax-invoice": {
        "/api/admin/receipts/{receiptId}/tax-invoice",
    },
    r"/api/admin/payments/scb/(PAY-SCB-[A-Z0-9-]+)/inquire": {
        "/api/admin/payments/scb/{paymentId}/inquire",
    },
    r"/api/orders/MPP-[A-Z0-9-]+/cancel": {
        "/api/orders/{orderId}/cancel",
    },
    r"/api/admin/document-requirements/([A-Za-z0-9_-]+)": {
        "/api/admin/document-requirements/{requirementId}",
    },
    r"(?:/api)?/documents/(DOC-[A-F0-9]+)": {
        "/api/documents/{documentId}",
    },
    r"/api/(admin|staff|kitchen)/orders/(MPP-[A-Z0-9-]+)": {
        "/api/admin/orders/{orderId}",
        "/api/staff/orders/{orderId}",
        "/api/kitchen/orders/{orderId}",
    },
    r"/api/(admin|staff)/deliveries/(MPP-[A-Z0-9-]+)": {
        "/api/admin/deliveries/{orderId}",
        "/api/staff/deliveries/{orderId}",
    },
    r"/api/admin/riders/(RDR-[A-Z0-9-]+)": {
        "/api/admin/riders/{riderId}",
    },
    r"/api/admin/rider-applications/(RAP-[A-Z0-9-]+)": {
        "/api/admin/rider-applications/{applicationId}",
    },
    r"/api/admin/merchant-applications/(MAP-[A-Z0-9-]+)": {
        "/api/admin/merchant-applications/{applicationId}",
    },
    r"/api/admin/menu/([a-z0-9-]+)": {
        "/api/admin/menu/{menuId}",
    },
}
PATH_VALUES = {
    "applicationId": "RAP-CONTRACT",
    "documentId": "DOC-AAAAAAAAAAAAAAAA",
    "menuId": "contract",
    "orderId": "MPP-CONTRACT",
    "paymentId": "PAY-SCB-CONTRACT",
    "provider": "grab",
    "receiptId": "RCT-CONTRACT",
    "requirementId": "contract",
    "riderId": "RDR-CONTRACT",
    "subject": "rider",
    "trackingCode": "TRK-" + "A" * 32,
}


class ContractServer(app.BoundedHTTPServer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.handler_errors = []

    def handle_error(self, request, client_address):
        self.handler_errors.append(client_address)


def resolve_pointer(document, reference):
    if not reference.startswith("#/"):
        raise AssertionError(f"Only local OpenAPI references are allowed: {reference}")
    value = document
    for token in reference[2:].split("/"):
        token = token.replace("~1", "/").replace("~0", "~")
        value = value[token]
    return value


def walk_references(document, value):
    if isinstance(value, dict):
        reference = value.get("$ref")
        if reference:
            resolve_pointer(document, reference)
        for child in value.values():
            walk_references(document, child)
    elif isinstance(value, list):
        for child in value:
            walk_references(document, child)


def runtime_operations():
    source = Path(app.__file__).read_text(encoding="utf-8")
    module = ast.parse(source)
    handler = next(
        node
        for node in module.body
        if isinstance(node, ast.ClassDef) and node.name == "Handler"
    )
    operations = set()
    unmapped = set()
    for function in handler.body:
        if not isinstance(function, ast.FunctionDef):
            continue
        method = HANDLER_METHODS.get(function.name)
        if not method:
            continue
        for node in ast.walk(function):
            if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
                continue
            value = node.value
            if "/api" not in value and value != "/auth/scb/callback":
                continue
            if value in {"/api/", "/api/admin/"}:
                continue
            if value.startswith("/api/") or value == "/auth/scb/callback":
                if not re.search(r"[()[\]|+?*\\]", value):
                    operations.add((method, value))
                    continue
            templates = RUNTIME_PATTERN_TEMPLATES.get(value)
            if templates:
                operations.update((method, template) for template in templates)
            else:
                unmapped.add((method, value))
    if unmapped:
        raise AssertionError(f"Unmapped runtime API route patterns: {sorted(unmapped)}")
    return operations


class OpenApiContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = yaml.safe_load(OPENAPI.read_text(encoding="utf-8"))
        cls.tmp = TemporaryDirectory()
        root = Path(cls.tmp.name)
        app.DATA, app.DB_PATH = root / "data", root / "data" / "contract.sqlite3"
        app.ADMIN_KEY = "contract-admin"
        app.EMPLOYEE_KEY = "contract-employee"
        app.KITCHEN_KEY = "contract-kitchen"
        app.initialise_database()
        cls.server = ContractServer(("127.0.0.1", 0), app.Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.origin = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)
        cls.tmp.cleanup()

    def test_contract_structure_references_and_security(self):
        document = self.contract
        self.assertEqual(document["openapi"], "3.1.0")
        self.assertTrue(document["info"]["title"])
        self.assertRegex(str(document["info"]["version"]), r"^\d+\.\d+\.\d+$")
        self.assertTrue(document["servers"])
        self.assertTrue(document["paths"])
        walk_references(document, document)

        schemes = document["components"]["securitySchemes"]
        for path, path_item in document["paths"].items():
            template_parameters = set(re.findall(r"{([^}]+)}", path))
            for method, operation in path_item.items():
                if method not in HTTP_METHODS:
                    continue
                with self.subTest(method=method, path=path):
                    self.assertTrue(operation.get("summary"))
                    self.assertTrue(operation.get("responses"))
                    declared = {
                        parameter["name"]
                        for parameter in operation.get("parameters", [])
                        if parameter.get("in") == "path" and parameter.get("required")
                    }
                    self.assertEqual(template_parameters, declared)
                    for requirement in operation.get("security", []):
                        self.assertLessEqual(set(requirement), set(schemes))
                    if path.startswith(("/api/admin/", "/api/staff/", "/api/kitchen/")):
                        self.assertTrue(operation.get("security"))

    def test_every_published_operation_is_recognized_by_the_server(self):
        generic_not_found = json.dumps(
            {"error": "ไม่พบ API"}, ensure_ascii=False, separators=(",", ":")
        )
        for path, path_item in self.contract["paths"].items():
            values = {
                **PATH_VALUES,
                "applicationId": (
                    "MAP-CONTRACT"
                    if "merchant-applications" in path
                    else "RAP-CONTRACT"
                ),
            }
            concrete = re.sub(
                r"{([^}]+)}",
                lambda match: values[match.group(1)],
                path,
            )
            for method in path_item:
                if method not in HTTP_METHODS:
                    continue
                body = b"{}" if method in {"post", "put", "patch"} else None
                request = Request(
                    self.origin + concrete,
                    data=body,
                    method=method.upper(),
                    headers={"Content-Type": "application/json"},
                )
                try:
                    with urlopen(request, timeout=3) as response:
                        status = response.status
                        payload = (
                            ""
                            if response.headers.get_content_type()
                            == "text/event-stream"
                            else response.read().decode()
                        )
                except HTTPError as error:
                    status = error.code
                    payload = error.read().decode()
                    error.close()
                with self.subTest(method=method, path=path, status=status):
                    self.assertNotEqual(status, 501)
                    compact = re.sub(r"\s+", "", payload)
                    self.assertNotEqual(compact, generic_not_found)
        self.assertEqual(self.server.handler_errors, [])

    def test_runtime_and_openapi_operations_have_reverse_parity(self):
        published = {
            (method, path)
            for path, path_item in self.contract["paths"].items()
            for method in path_item
            if method in HTTP_METHODS
        }
        self.assertEqual(runtime_operations(), published)


if __name__ == "__main__":
    unittest.main()
