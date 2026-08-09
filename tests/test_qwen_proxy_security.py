import unittest
import inspect

from app import Handler, qwen_proxy_target


class QwenProxySecurityTests(unittest.TestCase):
    def test_proxy_uses_a_fixed_connection_instead_of_urlopen_target(self):
        source = inspect.getsource(Handler.proxy_qwen_upstream)
        self.assertNotIn("urlopen(", source)
        self.assertIn("HTTPConnection", source)

    def test_proxy_target_keeps_the_reviewed_loopback_origin(self):
        self.assertEqual(
            qwen_proxy_target(
                "http://127.0.0.1:8091",
                "/v1/chat/completions",
                "model=qwen",
            ),
            "http://127.0.0.1:8091/v1/chat/completions?model=qwen",
        )

    def test_proxy_target_rejects_untrusted_origin_and_traversal(self):
        with self.assertRaises(ValueError):
            qwen_proxy_target("https://attacker.example", "/v1/models", "")
        with self.assertRaises(ValueError):
            qwen_proxy_target("http://127.0.0.1:8091", "/v1/../etc/passwd", "")
        with self.assertRaises(ValueError):
            qwen_proxy_target("http://127.0.0.1:8091", "/v1/%2e%2e/etc/passwd", "")


if __name__ == "__main__":
    unittest.main()
