import json
import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from scripts.ci import evidence


class InfrastructureEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.output = self.root / "reports"
        self.images = self.root / "images"
        self.schema = self.root / "schema"
        self.images.write_text(
            f"sha256:{'a' * 64}\nsha256:{'b' * 64}\n",
            encoding="utf-8",
        )
        self.previous_output = evidence.OUTPUT
        evidence.OUTPUT = self.output

    def tearDown(self):
        evidence.OUTPUT = self.previous_output
        self.tmp.cleanup()

    def run_evidence(self):
        with patch.dict(
            os.environ,
            {
                "IMAGE_EVIDENCE_FILE": str(self.images),
                "KUBERNETES_SCHEMA_EVIDENCE_FILE": str(self.schema),
            },
        ):
            result = evidence.infrastructure()
        report = json.loads(
            (self.output / "infrastructure.json").read_text(encoding="utf-8")
        )
        return result, report

    def test_missing_schema_proof_fails_closed(self):
        result, report = self.run_evidence()
        self.assertEqual(result, 1)
        self.assertEqual(report["status"], "fail")
        self.assertFalse(report["metrics"]["kubernetesSchemaValidated"])

    def test_valid_schema_proof_is_accepted(self):
        self.schema.write_text("c" * 64 + "\n", encoding="utf-8")
        result, report = self.run_evidence()
        self.assertEqual(result, 0)
        self.assertEqual(report["status"], "pass")
        self.assertTrue(report["metrics"]["kubernetesSchemaValidated"])


if __name__ == "__main__":
    unittest.main()
