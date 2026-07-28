#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
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

PORT="$(python3 - <<'PY'
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

python3 "$ROOT/app.py" >"$TMP_DIR/server.log" 2>&1 &
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
order_id="$(printf '%s' "$order" | python3 -c 'import json,sys; print(json.load(sys.stdin)["order"]["id"])')"

curl --silent --fail --max-time 3 --request POST "$BASE_URL/api/order-lookup" \
  --header 'Content-Type: application/json' \
  --data "{\"order_id\":\"$order_id\",\"phone\":\"0812345678\"}" >"$TMP_DIR/lookup.json"
cancelled="$(curl --silent --fail --max-time 3 --request POST "$BASE_URL/api/orders/$order_id/cancel" \
  --header 'Content-Type: application/json' \
  --data '{"phone":"0812345678"}')"
printf '%s' "$cancelled" | python3 -c 'import json,sys; assert json.load(sys.stdin)["order"]["status"] == "cancelled"'

admin_header="$(printf '%s' "$ADMIN_KEY" | base64 | tr -d '\n')"
curl --silent --fail --max-time 3 "$BASE_URL/api/admin/dashboard" \
  --header "X-Admin-Key-B64: $admin_header" >"$TMP_DIR/dashboard.json"
python3 - "$TMP_DIR/dashboard.json" <<'PY'
import json
import sys
data=json.load(open(sys.argv[1], encoding="utf-8"))
assert data["summary"]["orders"] == 1
assert data["orders"][0]["status"] == "cancelled"
PY

echo "Isolated API smoke checks passed."
