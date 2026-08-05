import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STACK = ROOT / "infrastructure" / "terraform" / "cloudflare"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class CloudflareTerraformTests(unittest.TestCase):
    def test_dns_records_are_proxied_tunnel_cnames(self):
        terraform = "\n".join(read(path) for path in sorted(STACK.glob("*.tf")))

        self.assertEqual(terraform.count('resource "cloudflare_dns_record"'), 11)
        self.assertEqual(terraform.count('type    = "CNAME"'), 11)
        self.assertEqual(terraform.count("content = local.tunnel_cname"), 11)
        self.assertEqual(terraform.count("proxied = true"), 11)
        self.assertEqual(terraform.count("ttl     = 1"), 11)

    def test_zdash_uses_loopback_gateway_and_cloudflare_access(self):
        main = read(STACK / "main.tf")
        zdash = read(STACK / "zdash.tf")
        outputs = read(STACK / "outputs.tf")

        self.assertIn('default     = "zdash.zeaz.dev"', zdash)
        self.assertIn('default     = "http://127.0.0.1:18080"', zdash)
        self.assertIn(
            'var.zdash_origin == "http://127.0.0.1:18080"', zdash
        )
        self.assertIn('resource "cloudflare_dns_record" "zdash"', zdash)
        self.assertIn(
            'resource "cloudflare_zero_trust_access_application" "zdash"',
            zdash,
        )
        self.assertIn('decision   = "allow"', zdash)
        self.assertIn("local.zdash_access_allowed_emails", zdash)
        self.assertIn(
            "var.zdash_access_allowed_emails : var.piewdash_access_allowed_emails",
            zdash,
        )
        self.assertIn(
            "var.zdash_hostname, service = var.zdash_origin", main
        )
        self.assertIn(
            "var.zdash_hostname, service = var.zdash_origin", outputs
        )
        self.assertIn('output "zdash_url"', zdash)
        self.assertIn('output "zdash_access_audience"', zdash)

    def test_zdash_plan_and_manual_ingress_examples_match(self):
        plan = read(ROOT / "scripts" / "cloudflare-plan.sh")
        ingress = read(
            ROOT / "deploy" / "cloudflared" / "moopiew-ingress.yml.example"
        )
        env_example = read(ROOT / ".env.cloudflare.example")
        tfvars_example = read(STACK / "terraform.tfvars.example")

        self.assertIn(
            'TF_VAR_zdash_hostname="${ZDASH_HOSTNAME:-zdash.zeaz.dev}"',
            plan,
        )
        self.assertIn(
            'TF_VAR_zdash_origin="${ZDASH_ORIGIN:-http://127.0.0.1:18080}"',
            plan,
        )
        self.assertIn("TF_VAR_zdash_access_allowed_emails", plan)
        self.assertIn("hostname: zdash.zeaz.dev", ingress)
        self.assertIn("service: http://127.0.0.1:18080", ingress)
        self.assertIn("ZDASH_HOSTNAME=zdash.zeaz.dev", env_example)
        self.assertIn("ZDASH_ORIGIN=http://127.0.0.1:18080", env_example)
        self.assertIn('zdash_hostname    = "zdash.zeaz.dev"', tfvars_example)
        self.assertIn(
            'zdash_origin      = "http://127.0.0.1:18080"',
            tfvars_example,
        )

    def test_existing_reviewed_origins_remain_intact(self):
        variables = read(STACK / "variables.tf")
        caddy = read(ROOT / "deploy" / "caddy" / "Caddyfile")
        ingress = read(
            ROOT / "deploy" / "cloudflared" / "moopiew-ingress.yml.example"
        )

        self.assertIn(
            'var.piewdash_origin == "http://127.0.0.1:80"', variables
        )
        self.assertNotIn('default     = "http://127.0.0.1:8082"', variables)
        self.assertIn("http://piewdash.zeaz.dev:80", caddy)
        self.assertIn("reverse_proxy 127.0.0.1:8082", caddy)
        self.assertIn("hostname: qwen.zeaz.dev", ingress)
        self.assertIn("service: http://127.0.0.1:8091", ingress)
        self.assertIn("hostname: chat.zeaz.dev", ingress)
        self.assertIn("service: http://127.0.0.1:3000", ingress)
        self.assertIn("hostname: zerp.zeaz.dev", ingress)

    def test_tunnel_configuration_remains_explicitly_opt_in(self):
        main = read(STACK / "main.tf")
        variables = read(STACK / "variables.tf")

        self.assertIn("count      = var.manage_tunnel_config ? 1 : 0", main)
        self.assertIn('default     = false', variables)
        self.assertIn('{ service = "http_status:404" }', main)
        self.assertLess(
            main.index("var.zdash_hostname, service = var.zdash_origin"),
            main.index('{ service = "http_status:404" }'),
        )


if __name__ == "__main__":
    unittest.main()
