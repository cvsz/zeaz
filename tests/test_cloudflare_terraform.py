import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STACK = ROOT / "infrastructure" / "terraform" / "cloudflare"


class CloudflareTerraformTests(unittest.TestCase):
    def test_public_dns_records_are_proxied_tunnel_cnames(self):
        main = (STACK / "main.tf").read_text(encoding="utf-8")

        self.assertEqual(main.count('type    = "CNAME"'), 4)
        self.assertEqual(main.count("content = local.tunnel_cname"), 4)
        self.assertEqual(main.count("proxied = true"), 4)
        self.assertEqual(main.count("ttl     = 1"), 4)

    def test_tunnel_origins_use_reviewed_caddy_proxies(self):
        variables = (STACK / "variables.tf").read_text(encoding="utf-8")
        plan = (ROOT / "scripts" / "cloudflare-plan.sh").read_text(
            encoding="utf-8"
        )
        ingress = (
            ROOT / "deploy" / "cloudflared" / "moopiew-ingress.yml.example"
        ).read_text(encoding="utf-8")

        self.assertIn('default     = "http://127.0.0.1:8080"', variables)
        self.assertIn(
            'var.moopiew_origin == "http://127.0.0.1:8080"', variables
        )
        self.assertIn('default     = "http://127.0.0.1:80"', variables)
        self.assertIn('var.piewdash_origin == "http://127.0.0.1:80"', variables)
        self.assertNotIn('default     = "http://127.0.0.1:8082"', variables)
        self.assertIn(
            'TF_VAR_piewdash_origin="${PIEWDASH_ORIGIN:-http://127.0.0.1:80}"',
            plan,
        )
        self.assertIn("hostname: moopiew.zeaz.dev", ingress)
        self.assertIn("service: http://127.0.0.1:8080", ingress)
        self.assertIn("hostname: piewdash.zeaz.dev", ingress)
        self.assertIn("service: http://127.0.0.1:80", ingress)
        self.assertIn("hostname: zerp.zeaz.dev", ingress)
        self.assertEqual(
            ingress.count("service: http://127.0.0.1:80\n"), 2
        )
        self.assertNotIn("service: http://127.0.0.1:8082", ingress)

    def test_cmeerp_dns_record_and_ingress_are_present(self):
        main = (STACK / "main.tf").read_text(encoding="utf-8")
        variables = (STACK / "variables.tf").read_text(encoding="utf-8")
        outputs = (STACK / "outputs.tf").read_text(encoding="utf-8")

        self.assertIn('resource "cloudflare_dns_record" "cmeerp"', main)
        self.assertIn('comment = "CME Pro ERP via Cloudflare Tunnel"', main)
        self.assertIn('var.cmeerp_hostname, service = var.cmeerp_origin', main)
        self.assertIn('default     = "cme.zeaz.dev"', variables)
        self.assertIn('default     = "http://127.0.0.1:8001"', variables)
        self.assertIn('output "cmeerp_url"', outputs)
        self.assertIn('"https://${var.cmeerp_hostname}"', outputs)

    def test_zerp_uses_caddy_proxy_instead_of_direct_dev_server(self):
        variables = (STACK / "variables.tf").read_text(encoding="utf-8")
        caddy = (ROOT / "deploy" / "caddy" / "Caddyfile").read_text(
            encoding="utf-8"
        )

        self.assertIn('default     = "zerp.zeaz.dev"', variables)
        self.assertIn('default     = "http://127.0.0.1:80"', variables)
        self.assertIn("http://zerp.zeaz.dev:80", caddy)
        self.assertIn("reverse_proxy 127.0.0.1:3001", caddy)

    def test_tunnel_configuration_remains_explicitly_opt_in(self):
        main = (STACK / "main.tf").read_text(encoding="utf-8")
        variables = (STACK / "variables.tf").read_text(encoding="utf-8")

        self.assertIn("count      = var.manage_tunnel_config ? 1 : 0", main)
        self.assertIn('default     = false', variables)
        self.assertIn('{ service = "http_status:404" }', main)


if __name__ == "__main__":
    unittest.main()
