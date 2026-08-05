import http.client
import threading
import unittest
from tempfile import TemporaryDirectory

import app


class SalesDemoTests(unittest.TestCase):
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

    def setUp(self):
        self.tmp = TemporaryDirectory()
        root = app.Path(self.tmp.name)
        app.DATA = root / "data"
        app.DB_PATH = root / "data" / "sales-demo.sqlite3"
        app.initialise_database()

    def tearDown(self):
        self.tmp.cleanup()

    def request(self, path: str):
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=3)
        connection.request("GET", path, headers={"Host": "zttshop.zeaz.dev"})
        response = connection.getresponse()
        body = response.read().decode("utf-8")
        headers = dict(response.getheaders())
        connection.close()
        return response.status, body, headers

    def test_demo_alias_redirects_to_published_react_entry(self):
        status, body, headers = self.request("/demo")
        self.assertEqual(status, 302)
        self.assertEqual(headers["Location"], "/platform/sales-demo.html")
        self.assertEqual(body, "")

    def test_published_demo_contains_customer_presentation_flow(self):
        status, body, _ = self.request("/platform/sales-demo.html")
        self.assertEqual(status, 200)
        self.assertIn("ZTT Shop Commerce OS", body)
        self.assertIn('type="module"', body)
        self.assertIn("/platform/assets/", body)

    def test_demo_source_contains_safe_sales_contract(self):
        source = (app.Path(__file__).parents[1] / "apps" / "web" / "src" / "sales-demo.tsx").read_text()
        self.assertIn("2 แถม 1", source)
        self.assertIn("990", source)
        self.assertIn("Facebook Messenger", source)
        self.assertIn("Shopee", source)
        self.assertIn("Human handoff", source)
        self.assertIn("ทดสอบการแพ้", source)

    def test_demo_styles_bound_mobile_grid_intrinsic_width(self):
        styles = (app.Path(__file__).parents[1] / "apps" / "web" / "src" / "sales-demo.css").read_text()
        self.assertIn(".sales-demo-app, .demo-sidebar, .demo-main, .demo-topbar, .demo-content, .demo-nav", styles)
        self.assertIn("min-width: 0", styles)
        self.assertIn(".sync-button span", styles)

    def test_sensitive_skin_guardrail_precedes_dryness_sales_reply(self):
        source = (app.Path(__file__).parents[1] / "apps" / "web" / "src" / "sales-demo.tsx").read_text()
        sensitivity = source.index('if (["แพ้", "แสบ", "ลอก"')
        dryness = source.index('if (["แห้ง", "ลอก", "ข้อศอก"')
        self.assertLess(sensitivity, dryness)


if __name__ == "__main__":
    unittest.main()
