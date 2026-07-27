#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python3 - "$ROOT" <<'PY'
import json, sys
from pathlib import Path

root = Path(sys.argv[1])
manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
missing = [name for name in manifest["required_files"] if not (root / name).is_file()]
required_directories = """branding/logo branding/brand-kit branding/app-icons branding/watermark
social/facebook social/instagram social/tiktok social/youtube social/line
ads/google/search ads/google/display ads/google/performance-max ads/meta/carousel ads/tiktok ads/campaign/launch ads/campaign/promotion ads/campaign/retargeting
print/menu print/restaurant print/packaging print/signage
food/categories/pork food/categories/chicken food/categories/seafood food/categories/drinks food/categories/desserts food/menu-items/original food/menu-items/thumbnail food/menu-items/optimized food/photography/hero food/photography/lifestyle food/photography/restaurant food/ai-generated/generated
icons/ui icons/food icons/social icons/system illustrations/onboarding illustrations/empty-state illustrations/marketing illustrations/characters videos/branding videos/marketing videos/social/reels videos/social/shorts videos/social/tiktok videos/tutorials""".split()
directories = [name for name in required_directories if not (root / name).is_dir()]
if missing or directories:
    if missing: print("Missing files: " + ", ".join(missing), file=sys.stderr)
    if directories: print("Missing directories: " + ", ".join(directories), file=sys.stderr)
    raise SystemExit(1)
for relative in ("manifest.json", "branding/brand-kit/colors.json", "branding/brand-kit/typography.json", "branding/brand-kit/spacing.json", "branding/brand-kit/design-token.json", "food/ai-generated/prompts.json"):
    json.loads((root / relative).read_text(encoding="utf-8"))
print("Asset package is valid.")
PY
