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
if [[ -d "$ROOT/node_modules" ]]; then (cd "$ROOT" && npm run typecheck); fi
echo "Platform checks passed."
