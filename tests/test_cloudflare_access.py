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

    def test_access_application_uses_exact_nonempty_email_allowlist(self):
        main = (
            ROOT / "infrastructure/terraform/cloudflare/main.tf"
        ).read_text(encoding="utf-8")
        variables = (
            ROOT / "infrastructure/terraform/cloudflare/variables.tf"
        ).read_text(encoding="utf-8")
        self.assertIn(
            'cloudflare_zero_trust_access_application" "piewdash', main
        )
        self.assertNotIn(
            'cloudflare_zero_trust_access_application" "qwen', main
        )
        self.assertIn("enable_binding_cookie      = true", main)
        self.assertIn("http_only_cookie_attribute = true", main)
        self.assertIn("piewdash_access_allowed_emails", main)
        self.assertIn(
            "length(var.piewdash_access_allowed_emails) > 0", variables
        )
        self.assertNotIn("everyone", main)


if __name__ == "__main__":
    unittest.main()
