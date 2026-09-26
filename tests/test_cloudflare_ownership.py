import re
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def tracked_files() -> list[str]:
    """Files git actually tracks.

    The guard has to describe the committed tree. A developer machine can still
    hold an ignored state file or a leftover provider directory from before the
    move, and that is not a duplicate declaration.
    """
    result = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files"],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.split()

# Every DNS record, tunnel ingress rule and Cloudflare Access application for
# *.zeaz.dev is declared in the zworkforce repository. The guards for those
# resources live there, next to the configuration they describe.
OWNING_REPOSITORY = "zworkforce"

# The local gateway and dashboard proxy still belong to this repository, so
# those checks stay here even though Cloudflare itself moved.
CADDY = ROOT / "deploy" / "caddy" / "Caddyfile"
DASHBOARD_UNIT = ROOT / "deploy" / "systemd" / "moopiew-proxy-system@.service"
PRODUCTION_CHECK = ROOT / "scripts" / "production-check.sh"

# Removed from this repository once ownership moved. A reappearance means a
# second stack is being declared for a record another repository owns.
REMOVED_SCRIPTS = (
    "scripts/cloudflare-apply.sh",
    "scripts/cloudflare-plan.sh",
    "scripts/cloudflare-state.sh",
    "scripts/cloudflare-tunnel.sh",
    "scripts/cloudflare-import-dns.sh",
    "scripts/lib/cloudflare-terraform-env.sh",
)

# The connector still runs on this host, so the host credential contract stays.
CREDENTIAL_KEYS = (
    "CLOUDFLARE_API_TOKEN",
    "CLOUDFLARE_ACCOUNT_ID",
    "CLOUDFLARE_ZONE_ID",
    "CLOUDFLARE_TUNNEL_ID",
    "CLOUDFLARE_TUNNEL_TOKEN",
)

# A declaration that would recreate a duplicate of an owned record.
TERRAFORM_DNS_MARKER = re.compile(
    r"resource\s+\"cloudflare_dns_record\"|"
    r"resource\s+\"cloudflare_tunnel\"|"
    r"cfargotunnel\.com"
)


def terraform_sources() -> list[Path]:
    return [
        ROOT / name
        for name in tracked_files()
        if name.startswith("infrastructure/") and name.endswith(".tf")
    ]


class CloudflareOwnershipTests(unittest.TestCase):
    """This repository must not declare Cloudflare resources it does not own."""

    def test_no_cloudflare_terraform_is_committed(self):
        committed = [
            name
            for name in tracked_files()
            if name.startswith("infrastructure/terraform")
        ]
        self.assertEqual(
            committed,
            [],
            f"Cloudflare Terraform moved to {OWNING_REPOSITORY}: {committed}",
        )

    def test_no_terraform_source_declares_a_cloudflare_resource(self):
        offenders = [
            str(path.relative_to(ROOT))
            for path in terraform_sources()
            if TERRAFORM_DNS_MARKER.search(path.read_text(encoding="utf-8"))
        ]
        self.assertEqual(
            offenders,
            [],
            f"DNS and tunnel resources are owned by {OWNING_REPOSITORY}: {offenders}",
        )

    def test_no_terraform_state_is_committed(self):
        committed = [
            name for name in tracked_files() if ".tfstate" in name
        ]
        self.assertEqual(committed, [], f"State belongs to {OWNING_REPOSITORY}.")

    def test_cloudflare_provisioning_scripts_are_absent(self):
        tracked = set(tracked_files())
        present = [name for name in REMOVED_SCRIPTS if name in tracked]
        self.assertEqual(
            present,
            [],
            f"Use the equivalents in {OWNING_REPOSITORY} instead of {present}.",
        )

    def test_no_script_still_drives_cloudflare_provisioning(self):
        tracked = [name for name in tracked_files() if name.startswith("scripts/")]
        offenders = []
        for name in tracked:
            if not name.endswith(".sh"):
                continue
            text = (ROOT / name).read_text(encoding="utf-8")
            if re.search(r"terraform\s+(apply|plan|import)", text):
                offenders.append(name)
        self.assertEqual(
            offenders,
            [],
            f"Terraform runs in {OWNING_REPOSITORY}, not here: {offenders}",
        )

    def test_documentation_points_at_the_owning_repository(self):
        docs = (
            ROOT / "docs" / "cloudflare-deployment.md",
            ROOT / "docs" / "zdash-cloudflare.md",
            ROOT / "RUNBOOK.md",
            ROOT / "OPERATIONS.md",
        )
        for doc in docs:
            with self.subTest(doc=doc.name):
                self.assertIn(
                    OWNING_REPOSITORY,
                    doc.read_text(encoding="utf-8"),
                    f"{doc.name} must say where Cloudflare is managed.",
                )

    def test_host_credential_contract_still_documented(self):
        # production-check.sh still verifies the connector credentials on this
        # host, so the example file must keep declaring every key it requires.
        example = (ROOT / ".env.cloudflare.example").read_text(encoding="utf-8")
        production_check = PRODUCTION_CHECK.read_text(encoding="utf-8")
        for key in CREDENTIAL_KEYS:
            with self.subTest(key=key):
                self.assertIn(key, example)
                self.assertIn(key, production_check)

    def test_real_cloudflare_credentials_are_never_committed(self):
        self.assertNotIn(
            ".env.cloudflare",
            tracked_files(),
            ".env.cloudflare is a local secret and must not be committed.",
        )

    def test_dashboard_proxy_still_requires_environment_backed_basic_auth(self):
        caddy = CADDY.read_text(encoding="utf-8")
        unit = DASHBOARD_UNIT.read_text(encoding="utf-8")
        production_check = PRODUCTION_CHECK.read_text(encoding="utf-8")
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
