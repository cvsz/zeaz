import base64
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.ci.generate_sbom import generate_npm_sbom


class SbomTests(unittest.TestCase):
    def test_generates_deterministic_cyclonedx_components(self):
        digest = bytes(range(64))
        lock = {
            "name": "example",
            "version": "1.2.3",
            "packages": {
                "": {"name": "example", "version": "1.2.3"},
                "node_modules/@scope/tool": {
                    "name": "@scope/tool",
                    "version": "2.0.0",
                    "dev": True,
                    "integrity": "sha512-" + base64.b64encode(digest).decode(),
                },
            },
        }
        with TemporaryDirectory() as directory:
            path = Path(directory) / "package-lock.json"
            path.write_text(json.dumps(lock), encoding="utf-8")
            first = generate_npm_sbom(path)
            second = generate_npm_sbom(path)
        self.assertEqual(first, second)
        self.assertEqual(first["bomFormat"], "CycloneDX")
        self.assertEqual(first["specVersion"], "1.6")
        self.assertEqual(first["metadata"]["component"]["name"], "example")
        self.assertEqual(len(first["components"]), 1)
        component = first["components"][0]
        self.assertEqual(component["purl"], "pkg:npm/%40scope/tool@2.0.0")
        self.assertEqual(component["scope"], "optional")
        self.assertEqual(component["hashes"][0]["content"], digest.hex().upper())

    def test_rejects_lockfile_without_package_inventory(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "package-lock.json"
            path.write_text('{"name":"example","version":"1.0.0"}', encoding="utf-8")
            with self.assertRaises(ValueError):
                generate_npm_sbom(path)


if __name__ == "__main__":
    unittest.main()
