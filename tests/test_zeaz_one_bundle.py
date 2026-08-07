import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "apps" / "zeaz-one"


class ZeazOneBundleTests(unittest.TestCase):
    def test_source_contains_required_deployment_files(self):
        required = {
            "docker-compose.yml",
            "Caddyfile",
            "public/one/index.html",
            "public/one/business/index.html",
            "public/one/privacy/index.html",
            "public/one/terms/index.html",
            "public/one/product-plan/index.html",
            "public/one/product.json",
            "public/support/zeaz-one/index.html",
            "api/product.json",
            "api/server.mjs",
        }
        missing = {path for path in required if not (SOURCE / path).is_file()}
        self.assertFalse(missing, missing)

    def test_services_bind_only_to_reviewed_loopback_ports(self):
        compose = (SOURCE / "docker-compose.yml").read_text(
            encoding="utf-8"
        )
        for port in (18081, 18082, 18083, 18084):
            self.assertIn("127.0.0.1:${", compose)
            self.assertIn(str(port), compose)
        self.assertNotIn('"0.0.0.0:', compose)

    def test_product_api_contains_three_models_and_public_source_matches(self):
        product = json.loads(
            (SOURCE / "api/product.json").read_text(encoding="utf-8")
        )
        public_product = json.loads(
            (SOURCE / "public/one/product.json").read_text(encoding="utf-8")
        )
        self.assertEqual(len(product["models"]), 3)
        self.assertEqual(product, public_product)

    def test_root_sync_is_atomic_and_does_not_require_remote_ssh(self):
        sync = (ROOT / "scripts" / "zeaz-one-sync.sh").read_text(
            encoding="utf-8"
        )
        self.assertIn("git -C \"$ROOT\" merge --ff-only origin/main", sync)
        self.assertIn('cp -a "$SOURCE_ROOT/." "$incoming/"', sync)
        self.assertIn("ln -sfn", sync)
        self.assertIn("mv -Tf", sync)
        self.assertIn("FORCE_ENABLE_ZEAZ_ONE_API_ROUTE=true", sync)
        self.assertNotIn("rsync", sync)
        self.assertNotIn("REMOTE=", sync)

    def test_canonical_urls_are_present(self):
        combined = "\n".join(
            path.read_text(encoding="utf-8")
            for suffix in ("*.html", "*.json", "*.yaml")
            for path in SOURCE.rglob(suffix)
        )
        for url in (
            "https://one.zeaz.dev",
            "https://www.zeaz.dev/products/zeaz-one",
            "https://api.zeaz.dev/v1/products/zeaz-one",
            "https://one.zeaz.dev/business",
            "https://one.zeaz.dev/privacy",
            "https://one.zeaz.dev/terms",
            "https://support.zeaz.dev/zeaz-one",
        ):
            self.assertIn(url, combined)


if __name__ == "__main__":
    unittest.main()
