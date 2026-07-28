import os
import subprocess
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]


class TerraformStateTests(unittest.TestCase):
    def test_r2_backend_enforces_encryption_and_lockfile(self):
        backend = (
            ROOT / "infrastructure/terraform/cloudflare/backend.r2.tf.example"
        ).read_text(encoding="utf-8")
        self.assertIn('backend "s3"', backend)
        self.assertIn("encrypt                     = true", backend)
        self.assertIn("use_lockfile                = true", backend)
        self.assertIn('key                         = "zeaz/cloudflare/terraform.tfstate"', backend)
        self.assertNotIn("access_key", backend)
        self.assertNotIn("secret_key", backend)

    def test_migration_is_fail_closed_and_verifies_remote_state(self):
        script = (ROOT / "scripts/cloudflare-state.sh").read_text(encoding="utf-8")
        self.assertIn('ALLOW_R2_WRITE:-false}" == "true"', script)
        self.assertIn("Cloudflare environment must not be group/world accessible", script)
        self.assertIn("init -migrate-state -force-copy", script)
        self.assertIn("install -m 600", script)
        self.assertIn('sha256sum "$backup"', script)
        self.assertIn('state pull > "$remote_state"', script)
        self.assertIn('diff -u "$before_addresses" "$after_addresses"', script)
        self.assertIn('install -m 600 "$backend_template" "$backend_file"', script)
        self.assertIn('rm -f "$backend_file"', script)
        self.assertLess(
            script.index('state list > "$before_addresses"'),
            script.index("  install_backend\n  \"$TF_BIN\""),
        )
        self.assertNotIn("CLOUDFLARE_ACCESS_SECRET_KEY=", script)

    def test_plan_does_not_silently_use_remote_backend(self):
        script = (ROOT / "scripts/cloudflare-plan.sh").read_text(encoding="utf-8")
        self.assertIn('TERRAFORM_BACKEND_TYPE:-local}" == "r2"', script)
        self.assertIn('"$ROOT/scripts/cloudflare-state.sh" init', script)
        self.assertIn('"$TF_BIN" -chdir="$STACK" init', script)
        self.assertNotIn("init -backend=false", script)

    def test_migration_control_flow_with_isolated_fake_backend(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            stack = root / "stack"
            backups = root / "backups"
            stack.mkdir()
            (stack / "terraform.tfstate").write_text(
                '{"version":4,"resources":[{"type":"example"}]}\n',
                encoding="utf-8",
            )
            (stack / "backend.r2.tf.example").write_text(
                (
                    ROOT
                    / "infrastructure/terraform/cloudflare/backend.r2.tf.example"
                ).read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            fake = root / "terraform"
            fake.write_text(
                """#!/usr/bin/env bash
set -Eeuo pipefail
case " $* " in
  *" state list "*) printf 'cloudflare_dns_record.moopiew\\n' ;;
  *" state pull "*) printf '{"version":4,"resources":[{"type":"cloudflare_dns_record"}]}\\n' ;;
  *" init -migrate-state -force-copy "*) exit 0 ;;
  *) exit 2 ;;
esac
""",
                encoding="utf-8",
            )
            fake.chmod(0o700)
            environment = root / "cloudflare.env"
            environment.write_text(
                "\n".join(
                    (
                        "TERRAFORM_BACKEND_TYPE=r2",
                        "ALLOW_R2_WRITE=true",
                        "CLOUDFLARE_ACCOUNT_ID=0123456789abcdef0123456789abcdef",
                        "TERRAFORM_STATE_BUCKET=zeaz-state-test",
                        "CLOUDFLARE_S3_API_ENDPOINT=https://0123456789abcdef0123456789abcdef.r2.cloudflarestorage.com",
                        "CLOUDFLARE_ACCESS_KEY_ID=test-access",
                        "CLOUDFLARE_ACCESS_SECRET_KEY=test-secret",
                        f"TERRAFORM_BIN={fake}",
                    )
                )
                + "\n",
                encoding="utf-8",
            )
            environment.chmod(0o600)
            result = subprocess.run(
                [str(ROOT / "scripts/cloudflare-state.sh"), "migrate"],
                cwd=ROOT,
                env={
                    **os.environ,
                    "CLOUDFLARE_ENV_FILE": str(environment),
                    "CLOUDFLARE_STACK_DIR": str(stack),
                    "CLOUDFLARE_STATE_BACKUP_DIR": str(backups),
                },
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((stack / "backend.tf").is_file())
            state_backups = list(backups.glob("*.tfstate"))
            self.assertEqual(len(state_backups), 1)
            self.assertEqual(state_backups[0].stat().st_mode & 0o777, 0o600)
            self.assertTrue(Path(str(state_backups[0]) + ".sha256").is_file())
            self.assertIn("migrate verification passed", result.stdout)


if __name__ == "__main__":
    unittest.main()
