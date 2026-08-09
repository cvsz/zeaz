import unittest
from pathlib import Path

SERVER_SOURCE = (Path(__file__).parents[1] / "arin_app" / "server.py").read_text()


class SecurityRegressionTests(unittest.TestCase):
    def test_response_paths_do_not_send_arbitrary_header_values(self):
        self.assertNotIn("self.send_header(key, value)", SERVER_SOURCE)

    def test_cookie_header_has_no_reusable_user_input_helper(self):
        self.assertNotIn("def session_cookie(", SERVER_SOURCE)
        self.assertNotIn("set_cookie: str | None", SERVER_SOURCE)

if __name__ == "__main__":
    unittest.main()
