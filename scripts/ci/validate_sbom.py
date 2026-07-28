#!/usr/bin/env python3
"""Validate a CycloneDX JSON document against its declared schema version."""
from __future__ import annotations

import argparse
from pathlib import Path

from cyclonedx.schema import SchemaVersion
from cyclonedx.validation.json import JsonStrictValidator


SCHEMA_VERSIONS = {
    "1.4": SchemaVersion.V1_4,
    "1.5": SchemaVersion.V1_5,
    "1.6": SchemaVersion.V1_6,
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("document", type=Path)
    parser.add_argument("--schema-version", choices=SCHEMA_VERSIONS, required=True)
    args = parser.parse_args()
    result = JsonStrictValidator(
        SCHEMA_VERSIONS[args.schema_version]
    ).validate_str(args.document.read_text(encoding="utf-8"), all_errors=True)
    if result:
        for error in result:
            print(error)
        return 1
    print(f"{args.document} is valid CycloneDX {args.schema_version} JSON.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
