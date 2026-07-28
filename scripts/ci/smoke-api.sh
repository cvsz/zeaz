#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PYTHON="${MOOPIEW_PYTHON:-$ROOT/.venv/bin/python}"
if [[ ! -x "$PYTHON" ]]; then
  PYTHON=python3
fi
TMP_DIR="$(mktemp -d)"
APP_PID=""

cleanup() {
  status="$?"
  if [[ -n "$APP_PID" ]] && kill -0 "$APP_PID" 2>/dev/null; then
    kill "$APP_PID" 2>/dev/null || true
    wait "$APP_PID" 2>/dev/null || true
  fi
  rm -rf -- "$TMP_DIR"
  exit "$status"
}
trap cleanup EXIT HUP INT TERM

PORT="$("$PYTHON" - <<'PY'
import socket
with socket.socket() as sock:
    sock.bind(("127.0.0.1", 0))
    print(sock.getsockname()[1])
PY
)"
BASE_URL="http://127.0.0.1:${PORT}"
export DATA_DIR="$TMP_DIR/data"
export DATABASE_PATH="$DATA_DIR/moopiew.sqlite3"
export PORT REQUIRE_ADMIN_KEY ADMIN_KEY EMPLOYEE_KEY KITCHEN_KEY
REQUIRE_ADMIN_KEY=true
ADMIN_KEY=ci-admin-key
EMPLOYEE_KEY=ci-employee-key
KITCHEN_KEY=ci-kitchen-key

"$PYTHON" "$ROOT/app.py" >"$TMP_DIR/server.log" 2>&1 &
APP_PID="$!"
for _ in {1..30}; do
  if curl --silent --fail --max-time 1 "$BASE_URL/api/health" >/dev/null; then break; fi
  sleep 0.1
done
curl --silent --fail --max-time 3 "$BASE_URL/api/health" >/dev/null

status="$(curl --silent --output "$TMP_DIR/admin.json" --write-out '%{http_code}' "$BASE_URL/api/admin/dashboard")"
[[ "$status" == "401" ]] || { echo "Unauthenticated admin endpoint returned $status" >&2; exit 1; }

curl --silent --fail --max-time 3 "$BASE_URL/api/menu" >"$TMP_DIR/menu.json"
pickup_date="$(date -u +%F)"
order="$(curl --silent --fail --max-time 3 --request POST "$BASE_URL/api/orders" \
  --header 'Content-Type: application/json' \
  --data "{\"name\":\"CI Customer\",\"phone\":\"0812345678\",\"pickup_date\":\"$pickup_date\",\"pickup_slot\":\"09:00–10:00\",\"payment_method\":\"cash\",\"items\":[{\"id\":\"classic\",\"quantity\":1}]}")"
order_id="$(printf '%s' "$order" | "$PYTHON" -c 'import json,sys; print(json.load(sys.stdin)["order"]["id"])')"
admin_header="$(printf '%s' "$ADMIN_KEY" | base64 | tr -d '\n')"

receipt="$(curl --silent --fail --max-time 3 --request POST "$BASE_URL/api/admin/orders/$order_id/receipt" \
  --header 'Content-Type: application/json' \
  --header "X-Admin-Key-B64: $admin_header" \
  --data '{}')"
receipt_id="$(printf '%s' "$receipt" | "$PYTHON" -c 'import json,sys; print(json.load(sys.stdin)["receipt"]["id"])')"
curl --silent --fail --max-time 3 --dump-header "$TMP_DIR/receipt.headers" \
  --output "$TMP_DIR/receipt.html" \
  "$BASE_URL/api/admin/receipts/$receipt_id/print" \
  --header "X-Admin-Key-B64: $admin_header"
"$PYTHON" - "$TMP_DIR/receipt.headers" "$TMP_DIR/receipt.html" <<'PY'
import re
import sys

headers = open(sys.argv[1], encoding="iso-8859-1").read()
body = open(sys.argv[2], encoding="utf-8").read()
csp = next((line.split(":", 1)[1].strip() for line in headers.splitlines() if line.lower().startswith("content-security-policy:")), "")
nonce = re.search(r"script-src 'self' 'nonce-([^']+)'", csp)
script = re.search(r"<script nonce='([^']+)'>", body)
assert nonce and script and nonce.group(1) == script.group(1)
assert "onclick=" not in body
assert "addEventListener('click',()=>window.print())" in body
PY

curl --silent --fail --max-time 3 --request POST "$BASE_URL/api/order-lookup" \
  --header 'Content-Type: application/json' \
  --data "{\"order_id\":\"$order_id\",\"phone\":\"0812345678\"}" >"$TMP_DIR/lookup.json"
cancelled="$(curl --silent --fail --max-time 3 --request POST "$BASE_URL/api/orders/$order_id/cancel" \
  --header 'Content-Type: application/json' \
  --data '{"phone":"0812345678"}')"
printf '%s' "$cancelled" | "$PYTHON" -c 'import json,sys; assert json.load(sys.stdin)["order"]["status"] == "cancelled"'
cancelled_lookup="$(curl --silent --fail --max-time 3 --request POST "$BASE_URL/api/order-lookup" \
  --header 'Content-Type: application/json' \
  --data "{\"order_id\":\"$order_id\",\"phone\":\"0812345678\"}")"
printf '%s' "$cancelled_lookup" | "$PYTHON" -c 'import json,sys; assert json.load(sys.stdin)["order"]["status"] == "cancelled"'

paid_order="$(curl --silent --fail --max-time 3 --request POST "$BASE_URL/api/orders" \
  --header 'Content-Type: application/json' \
  --data "{\"name\":\"Paid Customer\",\"phone\":\"0812345679\",\"pickup_date\":\"$pickup_date\",\"pickup_slot\":\"09:00–10:00\",\"payment_method\":\"cash\",\"items\":[{\"id\":\"classic\",\"quantity\":1}]}" )"
paid_order_id="$(printf '%s' "$paid_order" | "$PYTHON" -c 'import json,sys; print(json.load(sys.stdin)["order"]["id"])')"
"$PYTHON" - "$DATABASE_PATH" "$paid_order_id" <<'PY'
import sqlite3
import sys

with sqlite3.connect(sys.argv[1]) as connection:
    connection.execute("UPDATE orders SET payment_status='paid' WHERE id=?", (sys.argv[2],))
    connection.commit()
PY
paid_cancel_status="$(curl --silent --output "$TMP_DIR/paid-cancel.json" --write-out '%{http_code}' --max-time 3 --request POST "$BASE_URL/api/orders/$paid_order_id/cancel" \
  --header 'Content-Type: application/json' \
  --data '{"phone":"0812345679"}')"
[[ "$paid_cancel_status" == "400" ]]
printf '%s' "$(cat "$TMP_DIR/paid-cancel.json")" | "$PYTHON" -c 'import json,sys; assert "ชำระเงินแล้ว" in json.load(sys.stdin)["error"]'
admin_paid_cancel_status="$(curl --silent --output "$TMP_DIR/admin-paid-cancel.json" --write-out '%{http_code}' --max-time 3 --request PATCH "$BASE_URL/api/admin/orders/$paid_order_id" \
  --header 'Content-Type: application/json' \
  --header "X-Admin-Key-B64: $admin_header" \
  --data '{"status":"cancelled"}')"
[[ "$admin_paid_cancel_status" == "400" ]]
printf '%s' "$(cat "$TMP_DIR/admin-paid-cancel.json")" | "$PYTHON" -c 'import json,sys; assert "ชำระเงินแล้ว" in json.load(sys.stdin)["error"]'
admin_paid_pending_status="$(curl --silent --output "$TMP_DIR/admin-paid-pending.json" --write-out '%{http_code}' --max-time 3 --request PATCH "$BASE_URL/api/admin/orders/$paid_order_id" \
  --header 'Content-Type: application/json' \
  --header "X-Admin-Key-B64: $admin_header" \
  --data '{"payment_status":"pending"}')"
[[ "$admin_paid_pending_status" == "400" ]]
printf '%s' "$(cat "$TMP_DIR/admin-paid-pending.json")" | "$PYTHON" -c 'import json,sys; assert "ถอยกลับไม่ได้" in json.load(sys.stdin)["error"]'
cancelled_complete_status="$(curl --silent --output "$TMP_DIR/cancelled-complete.json" --write-out '%{http_code}' --max-time 3 --request PATCH "$BASE_URL/api/admin/orders/$order_id" \
  --header 'Content-Type: application/json' \
  --header "X-Admin-Key-B64: $admin_header" \
  --data '{"status":"completed"}')"
[[ "$cancelled_complete_status" == "400" ]]
printf '%s' "$(cat "$TMP_DIR/cancelled-complete.json")" | "$PYTHON" -c 'import json,sys; assert "ปิดแล้ว" in json.load(sys.stdin)["error"]'

curl --silent --fail --max-time 3 "$BASE_URL/api/admin/dashboard" \
  --header "X-Admin-Key-B64: $admin_header" >"$TMP_DIR/dashboard.json"
"$PYTHON" - "$TMP_DIR/dashboard.json" "$order_id" "$paid_order_id" <<'PY'
import json
import sys
data=json.load(open(sys.argv[1], encoding="utf-8"))
assert data["summary"]["orders"] == 2
orders={item["id"]: item for item in data["orders"]}
assert orders[sys.argv[2]]["status"] == "cancelled"
assert orders[sys.argv[3]]["status"] == "new"
assert orders[sys.argv[3]]["payment"]["status"] == "paid"
PY

echo "Isolated API smoke checks passed."
