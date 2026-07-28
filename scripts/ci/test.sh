#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
python3 -m py_compile "$ROOT/app.py"
if [[ "${SKIP_PYTHON_TESTS:-false}" != "true" ]]; then
  PYTHONPATH="$ROOT" python3 -m unittest discover -s "$ROOT/tests" -v
fi
ROOT="$ROOT" python3 - <<'PY'
import os
from pathlib import Path

document = (Path(os.environ["ROOT"]) / "docs/openapi.yaml").read_text(encoding="utf-8")
assert document.startswith("openapi: 3.1.0\n")
for path in (
    "/api/orders/{orderId}/cancel:",
    "/api/admin/dashboard:",
    "/api/admin/scb/auth/start:",
    "/api/admin/inventory/adjust:",
    "/api/admin/receipts/{receiptId}/print:",
    "/api/staff/orders/{orderId}:",
    "/api/kitchen/orders/{orderId}:",
):
    assert path in document, path
print("OpenAPI published-route coverage checks passed.")
PY
ROOT="$ROOT" python3 - <<'PY'
import os
import re
from pathlib import Path

root = Path(os.environ["ROOT"])
web = root / "web"
reference = re.compile(r'''(?:src|href)=["'](/[^"'#?]+)["']''')
for page in web.glob("*.html"):
    for target in reference.findall(page.read_text(encoding="utf-8")):
        if target.startswith("/api/") or target.startswith("/auth/"):
            continue
        relative = target.removeprefix("/")
        candidate = web / relative
        if target == "/":
            candidate = web / "index.html"
        elif target.endswith("/"):
            candidate /= "index.html"
        assert candidate.is_file(), f"{page.relative_to(root)} references missing {target}"
print("Static page asset-reference checks passed.")
PY
ROOT="$ROOT" python3 - <<'PY'
import os
import sys
from http.server import BaseHTTPRequestHandler
from email.message import Message

sys.path.insert(0, os.environ["ROOT"])
from app import Handler, valid_email

assert valid_email("merchant@example.co.th")
assert not valid_email("merchant@localhost")
assert not valid_email("merchant @example.com")
assert not valid_email("merchant@.example.com")
assert not valid_email("!" * 160 + "@example.com")

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
git -C "$ROOT" ls-files -z '*.js' | xargs -0 -r -n1 node --check
ROOT="$ROOT" python3 - <<'PY'
import os
from pathlib import Path

root = Path(os.environ["ROOT"])
app = (root / "web/app.js").read_text(encoding="utf-8")
page = (root / "web/index.html").read_text(encoding="utf-8")
for marker in ("/payments/scb/qr", "data:image/png;base64,", "payment-qr-status"):
    assert marker in app, marker
for marker in ("payment-qr-panel", "payment-qr", "payment-qr-status"):
    assert marker in page, marker
print("SCB QR checkout UI coverage checks passed.")
PY
ROOT="$ROOT" python3 - <<'PY'
import os
from pathlib import Path

source = (Path(os.environ["ROOT"]) / "scripts/sync-ai-credentials.sh").read_text(encoding="utf-8")
assert "Object.fromEntries(Object.entries(values).filter(([, value]) => value))" in source
assert "A required AI provider key is missing" not in source
print("Optional AI provider credential sync checks passed.")
PY
ROOT="$ROOT" python3 - <<'PY'
import os
from pathlib import Path

caddy = (Path(os.environ["ROOT"]) / "deploy/caddy/Caddyfile").read_text(encoding="utf-8")
assert "admin 127.0.0.1:2019" in caddy
assert 'geolocation=(self)' in caddy
print("Reverse proxy reload and geolocation policy checks passed.")
PY
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
expected={path.name for path in (root / "apps/web/dist/assets").iterdir() if path.is_file()}
published={path.name for path in (root / "web/platform/assets").iterdir() if path.is_file()}
assert published == expected, f"Stale or missing published platform assets: {sorted(published ^ expected)}"
print("Platform build publication checks passed.")
PY
fi
echo "Platform checks passed."
