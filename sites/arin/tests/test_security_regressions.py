import unittest

from arin_app.server import safe_header_items


class SecurityRegressionTests(unittest.TestCase):
    def test_response_headers_reject_control_characters(self):
        self.assertEqual(
            safe_header_items({"Cache-Control": "no-store"}),
            [("Cache-Control", "no-store")],
        )
        with self.assertRaises(ValueError):
            safe_header_items({"X-Test": "ok\r\nInjected: yes"})


if __name__ == "__main__":
    unittest.main()
