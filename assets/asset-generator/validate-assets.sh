#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python3 - "$ROOT" <<'PY'
import json, sys
from pathlib import Path

root = Path(sys.argv[1])
manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
missing = [name for name in manifest["required_files"] if not (root / name).is_file()]
directories = [name for name in manifest["directories"] if not (root / name).is_dir()]
if missing or directories:
    if missing: print("Missing files: " + ", ".join(missing), file=sys.stderr)
    if directories: print("Missing directories: " + ", ".join(directories), file=sys.stderr)
    raise SystemExit(1)
for relative in ("manifest.json", "brand-kit/colors.json", "brand-kit/typography.json", "food/ai-generated/prompts.json"):
    json.loads((root / relative).read_text(encoding="utf-8"))
print("Asset package is valid.")
PY
