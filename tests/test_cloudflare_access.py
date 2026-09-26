import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class CloudflareAccessTests(unittest.TestCase):
    def test_dashboard_proxy_requires_environment_backed_basic_auth(self):
        caddy = (ROOT / "deploy/caddy/Caddyfile").read_text(encoding="utf-8")
        unit = (
            ROOT / "deploy/systemd/moopiew-proxy-system@.service"
        ).read_text(encoding="utf-8")
        production_check = (
            ROOT / "scripts/production-check.sh"
        ).read_text(encoding="utf-8")
        self.assertRegex(
            caddy,
            re.compile(
                r"http://piewdash\.zeaz\.dev:80 \{.*?basicauth \{"
                r".*?\{\$PIEWDASH_BASIC_AUTH_USER\}"
                r".*?\{\$PIEWDASH_BASIC_AUTH_HASH\}",
                re.DOTALL,
            ),
        )
        self.assertIn("EnvironmentFile=/home/%i/zeaz/.env.dashboard", unit)
        self.assertNotIn("--environ", unit)
        self.assertIn("http://127.0.0.1/api/health", production_check)
        self.assertIn("cloudflareaccess.com/cdn-cgi/access/login/", production_check)


if __name__ == "__main__":
    unittest.main()
