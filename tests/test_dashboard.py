import json
import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from dashboard.api import health


class DashboardHealthTests(unittest.TestCase):
    def test_missing_reports_are_explicitly_unknown(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(health, "DATA", Path(directory)):
            result = health.snapshot()
        self.assertEqual(result["schemaVersion"], 1)
        self.assertTrue(all(report["status"] == "unknown" for report in result["reports"].values()))
        self.assertEqual(result["scores"]["evidenceCoverage"], 0)
        self.assertEqual(result["scores"]["productionReadiness"], 0)

    def test_report_requires_json_object(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(health, "DATA", Path(directory)):
            Path(directory, "ci.json").write_text("[]", encoding="utf-8")
            self.assertEqual(health._report("ci")["status"], "invalid")

    def test_valid_report_is_accepted(self):
        report = {
            "schemaVersion": 1,
            "status": "pass",
            "summary": "Checks passed.",
            "generatedAt": datetime.now(timezone.utc).isoformat(),
        }
        with tempfile.TemporaryDirectory() as directory, patch.object(health, "DATA", Path(directory)):
            Path(directory, "ci.json").write_text(json.dumps(report), encoding="utf-8")
            self.assertEqual(health._report("ci")["status"], "pass")

    def test_untrusted_status_is_invalid(self):
        report = {
            "schemaVersion": 1,
            "status": "pass evil",
            "summary": "<img src=x>",
            "generatedAt": datetime.now(timezone.utc).isoformat(),
        }
        with tempfile.TemporaryDirectory() as directory, patch.object(health, "DATA", Path(directory)):
            Path(directory, "ci.json").write_text(json.dumps(report), encoding="utf-8")
            self.assertEqual(health._report("ci")["status"], "invalid")

    def test_naive_or_future_report_timestamp_is_invalid(self):
        report = {
            "schemaVersion": 1,
            "status": "pass",
            "summary": "Checks passed.",
            "generatedAt": "2026-07-28T00:00:00",
        }
        with tempfile.TemporaryDirectory() as directory, patch.object(health, "DATA", Path(directory)):
            path = Path(directory, "ci.json")
            path.write_text(json.dumps(report), encoding="utf-8")
            self.assertEqual(health._report("ci")["status"], "invalid")
            report["generatedAt"] = (
                datetime.now(timezone.utc) + timedelta(hours=1)
            ).isoformat()
            path.write_text(json.dumps(report), encoding="utf-8")
            self.assertEqual(health._report("ci")["status"], "invalid")

    def test_coverage_score_uses_measured_percentage(self):
        report = {"status": "pass", "metrics": {"percent": 12.5}}
        self.assertEqual(health._report_score("coverage", report), 12.5)
        self.assertEqual(health._report_score("ci", report), 100)

    def test_health_output_is_json_serializable(self):
        json.dumps(health.snapshot())


if __name__ == "__main__":
    unittest.main()
