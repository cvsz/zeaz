import unittest

from scripts.ci.evidence import (
    _npm_audit_vulnerabilities,
    _python_audit_count,
)


class SecurityEvidenceTests(unittest.TestCase):
    def test_parses_scanner_metrics(self):
        npm = '{"metadata":{"vulnerabilities":{"high":1,"total":1}}}'
        python = (
            '{"dependencies":[{"name":"example","version":"1.0",'
            '"vulns":[{"id":"CVE-TEST"},{"id":"GHSA-TEST"}]}],"fixes":[]}'
        )
        self.assertEqual(_npm_audit_vulnerabilities(npm)["high"], 1)
        self.assertEqual(_python_audit_count(python), 2)

    def test_rejects_malformed_scanner_output(self):
        for output in ("", "{}", "[]", '{"metadata":{}}'):
            with self.subTest(scanner="npm", output=output):
                with self.assertRaises((KeyError, ValueError)):
                    _npm_audit_vulnerabilities(output)
        for output in ("", "{}", "null"):
            with self.subTest(scanner="python", output=output):
                with self.assertRaises(ValueError):
                    _python_audit_count(output)


if __name__ == "__main__":
    unittest.main()
