#!/usr/bin/env python3
"""Generate a deterministic CycloneDX inventory from an npm lockfile."""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
from pathlib import Path
from typing import Any
from urllib.parse import quote


def _component(path: str, package: dict[str, Any]) -> dict[str, Any] | None:
    name = package.get("name")
    version = package.get("version")
    if not isinstance(name, str) or not isinstance(version, str):
        return None
    purl = f"pkg:npm/{quote(name, safe='/')}@{quote(version, safe='')}"
    reference = f"urn:zeaz:npm:{hashlib.sha256(path.encode()).hexdigest()}"
    component: dict[str, Any] = {
        "type": "library",
        "bom-ref": reference,
        "name": name,
        "version": version,
        "purl": purl,
        "scope": "optional" if package.get("dev") or package.get("optional") else "required",
    }
    integrity = package.get("integrity", "")
    if isinstance(integrity, str):
        for digest in integrity.split():
            if digest.startswith("sha512-"):
                try:
                    value = base64.b64decode(digest.removeprefix("sha512-"), validate=True)
                except ValueError:
                    continue
                component["hashes"] = [{"alg": "SHA-512", "content": value.hex().upper()}]
                break
    return component


def generate_npm_sbom(lockfile: Path) -> dict[str, Any]:
    lock = json.loads(lockfile.read_text(encoding="utf-8"))
    packages = lock.get("packages")
    if not isinstance(packages, dict):
        raise ValueError("package-lock.json must contain a packages object")
    root = packages.get("", {})
    root_name = root.get("name", lock.get("name"))
    root_version = root.get("version", lock.get("version"))
    if not isinstance(root_name, str) or not isinstance(root_version, str):
        raise ValueError("package-lock.json must declare the root name and version")
    components = [
        component
        for path, package in sorted(packages.items())
        if path and isinstance(package, dict)
        if (component := _component(path, package)) is not None
    ]
    return {
        "$schema": "https://cyclonedx.org/schema/bom-1.6.schema.json",
        "bomFormat": "CycloneDX",
        "specVersion": "1.6",
        "version": 1,
        "metadata": {
            "component": {
                "type": "application",
                "bom-ref": f"pkg:npm/{quote(root_name, safe='/')}@{quote(root_version, safe='')}",
                "name": root_name,
                "version": root_version,
            },
            "tools": {
                "components": [
                    {
                        "type": "application",
                        "name": "zeaz-npm-lock-sbom",
                        "version": "1",
                    }
                ]
            },
        },
        "components": components,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lockfile", type=Path, default=Path("package-lock.json"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    document = generate_npm_sbom(args.lockfile)
    args.output.write_text(
        json.dumps(document, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(document['components'])} npm components to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
