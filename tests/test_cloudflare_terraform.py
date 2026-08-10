import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STACK = ROOT / "infrastructure" / "terraform" / "cloudflare"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class CloudflareTerraformTests(unittest.TestCase):
    def test_dns_records_are_proxied_tunnel_cnames(self):
        terraform = "\n".join(read(path) for path in sorted(STACK.glob("*.tf")))

        self.assertEqual(terraform.count('resource "cloudflare_dns_record"'), 20)
        self.assertEqual(terraform.count('type    = "CNAME"'), 20)
        self.assertEqual(terraform.count("content = local.tunnel_cname"), 20)
        self.assertEqual(terraform.count("proxied = true"), 20)
        self.assertEqual(terraform.count("ttl     = 1"), 20)

    def test_uperfect_route_uses_dedicated_lan_origin(self):
        main = read(STACK / "main.tf")
        outputs = read(STACK / "outputs.tf")
        uperfect = read(STACK / "uperfect.tf")
        plan = read(ROOT / "scripts" / "cloudflare-plan.sh")
        loader = read(ROOT / "scripts" / "lib" / "cloudflare-terraform-env.sh")
        importer = read(ROOT / "scripts" / "cloudflare-import-dns.sh")
        ingress = read(
            ROOT / "deploy" / "cloudflared" / "moopiew-ingress.yml.example"
        )
        env_example = read(ROOT / ".env.cloudflare.example")
        tfvars_example = read(STACK / "terraform.tfvars.example")

        self.assertIn('default     = "uperfect.zeaz.dev"', uperfect)
        self.assertIn('default     = "http://192.168.74.130:18765"', uperfect)
        self.assertIn(
            'var.uperfect_origin == "http://192.168.74.130:18765"', uperfect
        )
        self.assertIn('resource "cloudflare_dns_record" "uperfect"', uperfect)
        self.assertIn("var.uperfect_hostname, service = var.uperfect_origin", main)
        self.assertIn("var.uperfect_hostname, service = var.uperfect_origin", outputs)
        self.assertIn('output "uperfect_url"', uperfect)
        self.assertIn(
            'TF_VAR_uperfect_hostname="${UPERFECT_HOSTNAME:-uperfect.zeaz.dev}"',
            plan,
        )
        self.assertIn(
            'TF_VAR_uperfect_origin="${UPERFECT_ORIGIN:-http://192.168.74.130:18765}"',
            plan,
        )
        self.assertIn(
            'TF_VAR_uperfect_hostname="${UPERFECT_HOSTNAME:-uperfect.zeaz.dev}"',
            loader,
        )
        self.assertIn('[uperfect]="cloudflare_dns_record.uperfect"', importer)
        self.assertIn("hostname: uperfect.zeaz.dev", ingress)
        self.assertIn("service: http://192.168.74.130:18765", ingress)
        self.assertIn("UPERFECT_HOSTNAME=uperfect.zeaz.dev", env_example)
        self.assertIn("UPERFECT_ORIGIN=http://192.168.74.130:18765", env_example)
        self.assertIn('uperfect_hostname = "uperfect.zeaz.dev"', tfvars_example)
        self.assertIn('uperfect_origin   = "http://192.168.74.130:18765"', tfvars_example)

    def test_zok_route_uses_vite_ui_and_private_api_proxy(self):
        main = read(STACK / "main.tf")
        outputs = read(STACK / "outputs.tf")
        zok = read(STACK / "zok.tf")
        plan = read(ROOT / "scripts" / "cloudflare-plan.sh")
        loader = read(ROOT / "scripts" / "lib" / "cloudflare-terraform-env.sh")
        importer = read(ROOT / "scripts" / "cloudflare-import-dns.sh")
        ingress = read(
            ROOT / "deploy" / "cloudflared" / "moopiew-ingress.yml.example"
        )
        env_example = read(ROOT / ".env.cloudflare.example")
        tfvars_example = read(STACK / "terraform.tfvars.example")
        vite_config = read(Path("/mnt/zok/vite.config.js"))

        self.assertIn('default     = "zok.zeaz.dev"', zok)
        self.assertIn('default     = "http://127.0.0.1:5175"', zok)
        self.assertIn('var.zok_origin == "http://127.0.0.1:5175"', zok)
        self.assertIn('resource "cloudflare_dns_record" "zok"', zok)
        self.assertIn("var.zok_hostname, service = var.zok_origin", main)
        self.assertIn("var.zok_hostname, service = var.zok_origin", outputs)
        self.assertIn('output "zok_url"', zok)
        self.assertIn(
            'TF_VAR_zok_hostname="${ZOK_HOSTNAME:-zok.zeaz.dev}"',
            plan,
        )
        self.assertIn(
            'TF_VAR_zok_origin="${ZOK_ORIGIN:-http://127.0.0.1:5175}"',
            plan,
        )
        self.assertIn(
            'TF_VAR_zok_hostname="${ZOK_HOSTNAME:-zok.zeaz.dev}"',
            loader,
        )
        self.assertIn(
            'TF_VAR_zok_origin="${ZOK_ORIGIN:-http://127.0.0.1:5175}"',
            loader,
        )
        self.assertIn('[zok]="cloudflare_dns_record.zok"', importer)
        self.assertIn("hostname: zok.zeaz.dev", ingress)
        self.assertIn("service: http://127.0.0.1:5175", ingress)
        self.assertIn("ZOK_HOSTNAME=zok.zeaz.dev", env_example)
        self.assertIn("ZOK_ORIGIN=http://127.0.0.1:5175", env_example)
        self.assertIn('zok_hostname      = "zok.zeaz.dev"', tfvars_example)
        self.assertIn('zok_origin        = "http://127.0.0.1:5175"', tfvars_example)
        self.assertIn("target: 'http://127.0.0.1:3005'", vite_config)
        self.assertIn("allowedHosts: ['zok.zeaz.dev']", vite_config)

    def test_z_spark_route_serves_built_ui_and_private_api_proxy(self):
        main = read(STACK / "main.tf")
        outputs = read(STACK / "outputs.tf")
        z_spark = read(STACK / "z-spark.tf")
        plan = read(ROOT / "scripts" / "cloudflare-plan.sh")
        loader = read(ROOT / "scripts" / "lib" / "cloudflare-terraform-env.sh")
        importer = read(ROOT / "scripts" / "cloudflare-import-dns.sh")
        ingress = read(
            ROOT / "deploy" / "cloudflared" / "moopiew-ingress.yml.example"
        )
        env_example = read(ROOT / ".env.cloudflare.example")
        tfvars_example = read(STACK / "terraform.tfvars.example")
        caddy = read(ROOT / "deploy" / "caddy" / "Caddyfile")
        client = read(Path("/mnt/z-spark/client/src/App.jsx"))

        self.assertIn('default     = "z-spark.zeaz.dev"', z_spark)
        self.assertIn('default     = "http://127.0.0.1:8080"', z_spark)
        self.assertIn('var.z_spark_origin == "http://127.0.0.1:8080"', z_spark)
        self.assertIn('resource "cloudflare_dns_record" "z_spark"', z_spark)
        self.assertIn("var.z_spark_hostname, service = var.z_spark_origin", main)
        self.assertIn("var.z_spark_hostname, service = var.z_spark_origin", outputs)
        self.assertIn('output "z_spark_url"', z_spark)
        self.assertIn(
            'TF_VAR_z_spark_hostname="${Z_SPARK_HOSTNAME:-z-spark.zeaz.dev}"',
            plan,
        )
        self.assertIn(
            'TF_VAR_z_spark_origin="${Z_SPARK_ORIGIN:-http://127.0.0.1:8080}"',
            plan,
        )
        self.assertIn(
            'TF_VAR_z_spark_hostname="${Z_SPARK_HOSTNAME:-z-spark.zeaz.dev}"',
            loader,
        )
        self.assertIn(
            'TF_VAR_z_spark_origin="${Z_SPARK_ORIGIN:-http://127.0.0.1:8080}"',
            loader,
        )
        self.assertIn('[z-spark]="cloudflare_dns_record.z_spark"', importer)
        self.assertIn("hostname: z-spark.zeaz.dev", ingress)
        self.assertIn("service: http://127.0.0.1:8080", ingress)
        self.assertIn("Z_SPARK_HOSTNAME=z-spark.zeaz.dev", env_example)
        self.assertIn("Z_SPARK_ORIGIN=http://127.0.0.1:8080", env_example)
        self.assertIn('z_spark_hostname  = "z-spark.zeaz.dev"', tfvars_example)
        self.assertIn('z_spark_origin    = "http://127.0.0.1:8080"', tfvars_example)
        self.assertIn("http://z-spark.zeaz.dev:8080", caddy)
        self.assertIn("root * /mnt/z-spark/client/dist", caddy)
        self.assertIn("reverse_proxy 127.0.0.1:13131", caddy)
        self.assertIn("fetch('/api/chat'", client)

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
        self.assertIn('[{ service = "http_status:404" }]', main)
        self.assertLess(
            main.index("var.zdash_hostname, service = var.zdash_origin"),
            main.index('[{ service = "http_status:404" }]'),
        )

    def test_zeaz_one_is_opt_in_and_loopback_only(self):
        zeaz_one = read(STACK / "zeaz-one.tf")
        main = read(STACK / "main.tf")
        outputs = read(STACK / "outputs.tf")

        self.assertIn('variable "enable_zeaz_one"', zeaz_one)
        self.assertGreaterEqual(zeaz_one.count('default     = false'), 2)
        self.assertIn('default     = "one.zeaz.dev"', zeaz_one)
        self.assertIn('default     = "http://127.0.0.1:18081"', zeaz_one)
        self.assertIn('default     = "api.zeaz.dev"', zeaz_one)
        self.assertIn('default     = "http://127.0.0.1:18084"', zeaz_one)
        self.assertIn('default     = "support.zeaz.dev"', zeaz_one)
        self.assertIn('default     = "http://127.0.0.1:18083"', zeaz_one)
        self.assertEqual(zeaz_one.count("count   = var.enable_zeaz_one ? 1 : 0"), 2)
        self.assertIn("local.zeaz_one_ingress", main)
        self.assertIn("local.zeaz_one_ingress", outputs)

    def test_shared_api_is_path_specific_and_dns_is_not_replaced(self):
        zeaz_one = read(STACK / "zeaz-one.tf")
        api_worker = read(STACK / "workers" / "zeaz-one-product-api.js")
        ingress = read(
            ROOT / "deploy" / "cloudflared" / "moopiew-ingress.yml.example"
        )
        importer = read(ROOT / "scripts" / "cloudflare-import-dns.sh")

        self.assertNotIn('resource "cloudflare_dns_record" "zeaz_one_api"', zeaz_one)
        self.assertNotIn("hostname: api.zeaz.dev", ingress)
        self.assertNotIn("cloudflare_dns_record.zeaz_one_api", importer)
        gate = "var.enable_zeaz_one && var.enable_zeaz_one_api_route ? 1 : 0"
        self.assertEqual(zeaz_one.count(gate), 2)
        self.assertIn(
            'pattern = "${var.zeaz_one_api_hostname}/v1/products/zeaz-one*"',
            zeaz_one,
        )
        self.assertIn('const PRODUCT_SOURCE = "https://one.zeaz.dev/product.json";', api_worker)
        self.assertIn("cacheEverything: true", api_worker)

    def test_corporate_www_is_not_managed_by_this_stack(self):
        zeaz_one = read(STACK / "zeaz-one.tf")
        sync = read(ROOT / "scripts" / "zeaz-one-sync.sh")
        plan = read(ROOT / "scripts" / "cloudflare-plan.sh")
        loader = read(ROOT / "scripts" / "lib" / "cloudflare-terraform-env.sh")

        self.assertNotIn("enable_zeaz_one_www_redirect", zeaz_one)
        self.assertNotIn(
            'resource "cloudflare_workers_route" "zeaz_one_www_redirect"',
            zeaz_one,
        )
        self.assertNotIn("zeaz-one-www-redirect", zeaz_one)
        self.assertNotIn("--www-redirect", sync)
        self.assertNotIn("ZEAZ_ONE_WWW_REDIRECT", plan)
        self.assertNotIn("ZEAZ_ONE_WWW_REDIRECT", loader)
        self.assertFalse((STACK / "workers" / "zeaz-one-www-redirect.js").exists())

    def test_zeaz_one_scripts_and_examples_match(self):
        plan = read(ROOT / "scripts" / "cloudflare-plan.sh")
        loader = read(ROOT / "scripts" / "lib" / "cloudflare-terraform-env.sh")
        importer = read(ROOT / "scripts" / "cloudflare-import-dns.sh")
        apply = read(ROOT / "scripts" / "cloudflare-apply.sh")
        ingress = read(
            ROOT / "deploy" / "cloudflared" / "moopiew-ingress.yml.example"
        )
        env_example = read(ROOT / ".env.cloudflare.example")
        tfvars_example = read(STACK / "terraform.tfvars.example")

        for text in (plan, loader):
            self.assertIn("TF_VAR_enable_zeaz_one", text)
            self.assertIn("TF_VAR_enable_zeaz_one_api_route", text)
            self.assertIn("TF_VAR_zeaz_one_origin", text)
            self.assertIn("TF_VAR_zeaz_one_api_origin", text)
            self.assertIn("TF_VAR_zeaz_one_support_origin", text)
            self.assertNotIn("TF_VAR_enable_zeaz_one_www_redirect", text)
        self.assertIn('[zeaz-one]="cloudflare_dns_record.zeaz_one[0]"', importer)
        self.assertIn("--zeaz-one", apply)
        self.assertIn("FORCE_ENABLE_ZEAZ_ONE_API_ROUTE=true", apply)
        self.assertIn("hostname: one.zeaz.dev", ingress)
        self.assertIn("service: http://127.0.0.1:18081", ingress)
        self.assertIn("ZEAZ_ONE_ENABLED=false", env_example)
        self.assertIn("ZEAZ_ONE_API_ROUTE_ENABLED=false", env_example)
        self.assertNotIn("ZEAZ_ONE_WWW_REDIRECT_ENABLED", env_example)
        self.assertIn("enable_zeaz_one_api_route = false", tfvars_example)
        self.assertNotIn("enable_zeaz_one_www_redirect", tfvars_example)


if __name__ == "__main__":
    unittest.main()
