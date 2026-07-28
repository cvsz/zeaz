import os
import subprocess
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from cryptography.fernet import Fernet


ROOT = Path(__file__).resolve().parents[1]


class ScbPreflightTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.application = self.root / "application.env"
        self.payment = self.root / "payment.env"
        self.application.write_text(
            "ADMIN_KEY=test-admin\nPAYMENTS_ENABLED=false\n",
            encoding="utf-8",
        )

    def tearDown(self):
        self.tmp.cleanup()

    def run_preflight(self, pkce_field="codeVerifier"):
        self.payment.write_text(
            "\n".join(
                [
                    "PAYMENT_ENVIRONMENT=sandbox",
                    "SCB_ENABLED=false",
                    "SCB_PRODUCT=qr_api",
                    "SCB_OAUTH_MODE=authorization_code",
                    "SCB_PAYMENT_OAUTH_MODE=client_credentials",
                    "SCB_OAUTH_PKCE_ENABLED=true",
                    f"SCB_OAUTH_PKCE_TOKEN_FIELD={pkce_field}",
                    "SCB_API_KEY=test-key",
                    "SCB_API_SECRET=test-secret",
                    "SCB_BILLER_ID=test-biller",
                    "SCB_QR_CREATE_ENDPOINT=https://sandbox.example/qr",
                    "SCB_QR_INQUIRY_ENDPOINT=https://sandbox.example/inquiry",
                    "SCB_PAYMENT_CONFIRMATION_URL=https://example.test/callback",
                    "SCB_AUTHORIZE_ENDPOINT=https://sandbox.example/authorize",
                    "SCB_OAUTH_TOKEN_ENDPOINT=https://sandbox.example/token",
                    "SCB_MTLS_REQUIRED=false",
                    f"SCB_TOKEN_ENCRYPTION_KEY={Fernet.generate_key().decode()}",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return subprocess.run(
            ["bash", str(ROOT / "scripts/scb-preflight.sh")],
            cwd=ROOT,
            env={
                **os.environ,
                "MOOPIEW_ENV_FILE": str(self.application),
                "MOOPIEW_PAYMENT_ENV_FILE": str(self.payment),
            },
            capture_output=True,
            text=True,
        )

    def test_disabled_sandbox_configuration_passes_without_live_calls(self):
        result = self.run_preflight()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("payments remain safely disabled", result.stdout)

    def test_unapproved_pkce_field_fails_closed(self):
        result = self.run_preflight("unreviewedField")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("must be codeVerifier or code_verifier", result.stderr)


if __name__ == "__main__":
    unittest.main()
