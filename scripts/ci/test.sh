#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
python3 -m py_compile "$ROOT/app.py"
ROOT="$ROOT" python3 - <<'PY'
import os
import sys
from http.server import BaseHTTPRequestHandler
from email.message import Message

sys.path.insert(0, os.environ["ROOT"])
from app import Handler

def csp_for(nonce: str) -> str:
    handler = Handler.__new__(Handler)
    handler.path = "/api/admin/receipts/RCT-TEST/print"
    headers = []
    handler.send_header = lambda key, value: headers.append((key, value))
    handler._script_nonce = nonce
    original = BaseHTTPRequestHandler.end_headers
    BaseHTTPRequestHandler.end_headers = lambda self: None
    try:
        Handler.end_headers(handler)
    finally:
        BaseHTTPRequestHandler.end_headers = original
    return dict(headers)["Content-Security-Policy"]

assert "'nonce-test-nonce'" in csp_for("test-nonce")
assert "'nonce-" not in csp_for("")

rate_handler = Handler.__new__(Handler)
rate_handler.client_address = ("198.51.100.7", 0)
rate_handler.headers = Message()
for _ in range(120):
    assert rate_handler.rate("public")
assert not rate_handler.rate("public")
from app import RATE_BUCKETS
RATE_BUCKETS.clear()
print("CSP nonce and rate-limit regression checks passed.")
PY
node --check "$ROOT/web/app.js"
node --check "$ROOT/web/admin.js"
node --check "$ROOT/web/ops.js"
node --check "$ROOT/web/menu-preview.js"
node --check "$ROOT/web/api-monitor.js"
if [[ -d "$ROOT/node_modules" ]]; then
  (cd "$ROOT" && npm run typecheck && npm run build)
  cmp --silent "$ROOT/apps/web/dist/index.html" "$ROOT/web/platform/index.html" || {
    echo "web/platform is not synchronized with apps/web/dist; publish the current build before committing." >&2
    exit 1
  }
  ROOT="$ROOT" python3 - <<'PY'
import os
import re
from pathlib import Path

root=Path(os.environ["ROOT"])
index=(root / "apps/web/dist/index.html").read_text()
assets=re.findall(r'''/(?:platform/)?assets/([^"']+)''', index)
assert assets, "No built platform assets found"
for asset in assets:
    assert (root / "apps/web/dist/assets" / asset).is_file(), asset
    assert (root / "web/platform/assets" / asset).is_file(), asset
print("Platform build publication checks passed.")
PY
fi
echo "Platform checks passed."
