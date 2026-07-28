#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP_DIR="$(mktemp -d)"
PID=""
cleanup(){ [[ -z "$PID" ]] || kill "$PID" 2>/dev/null || true; rm -rf "$TMP_DIR"; }
trap cleanup EXIT
PORT="$(python3 - <<'PY'
import socket
with socket.socket() as sock:
    sock.bind(("127.0.0.1", 0))
    print(sock.getsockname()[1])
PY
)"
DATA_DIR="$TMP_DIR/data" DATABASE_PATH="$TMP_DIR/data/moopiew.sqlite3" PORT="$PORT" HOST=127.0.0.1 \
  "$ROOT/.venv/bin/python" "$ROOT/app.py" >"$TMP_DIR/server.log" 2>&1 & PID=$!
ready=false
for _ in {1..30}; do
  if curl -fsS --max-time 1 "http://127.0.0.1:$PORT/api/health" >/dev/null 2>&1; then ready=true; break; fi
  sleep .1
done
$ready || { echo "Benchmark server did not become ready." >&2; exit 1; }
times="$TMP_DIR/times"
for _ in $(seq 1 20); do curl -sS -o /dev/null -w '%{time_total}\n' "http://127.0.0.1:$PORT/api/health"; done | sort -n >"$times"
python3 - "$times" <<'PY'
import statistics, sys
values=[float(line) for line in open(sys.argv[1], encoding="ascii")]
percentile=values[max(0, int(len(values)*.95)-1)]
print(f"health requests={len(values)} mean={statistics.mean(values):.4f}s p95={percentile:.4f}s max={max(values):.4f}s")
PY
