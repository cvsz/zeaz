#!/usr/bin/env bash
# Universal Cross-Platform Installer & Maintenance Utility for macOS, Linux, and WSL
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERSION="1.0.0"

echo "=========================================================="
echo "    ZEAZ Universal Cross-Platform Setup & Update v${VERSION}   "
echo "=========================================================="
echo "Target Root: $ROOT"
echo "OS Detected: $(uname -s) ($(uname -m))"
echo

# 1. Environment & Prerequisite Checks
log() { printf '[%s] [ZEAZ-SETUP-%s] %s\n' "$(date +'%Y-%m-%d %H:%M:%S')" "$1" "$2"; }

log "INFO" "Checking System Runtime Prerequisites..."
command -v python3 >/dev/null 2>&1 || { log "ERROR" "Python 3.11+ is required"; exit 1; }
python3 -c 'import sys; raise SystemExit(sys.version_info < (3, 11))' || { log "ERROR" "Python version must be >= 3.11"; exit 1; }

HAS_NODE=true
command -v node >/dev/null 2>&1 || HAS_NODE=false
command -v npm >/dev/null 2>&1 || HAS_NODE=false

if [ "$HAS_NODE" = true ]; then
  log "INFO" "Node.js: $(node --version)"
  log "INFO" "NPM: $(npm --version)"
else
  log "WARN" "Node.js/NPM not found in PATH. Pre-compiled distribution bundles will be used."
fi

# 2. Virtual Environment Setup & Python Dependencies
log "INFO" "Setting up Python Virtual Environment (.venv)..."
if [ ! -d "$ROOT/.venv" ]; then
  python3 -m venv "$ROOT/.venv"
fi
"$ROOT/.venv/bin/pip" install --disable-pip-version-check -q -r "$ROOT/requirements.txt" || true

# 3. Node.js Monorepo Build (if Node is available)
if [ "$HAS_NODE" = true ]; then
  log "INFO" "Installing Node Monorepo Dependencies..."
  (cd "$ROOT" && npm install --no-audit --no-fund)
  log "INFO" "Building Production Frontend Assets (Vite & Turbo)..."
  (cd "$ROOT" && npm run build)
fi

# 4. Environment Configurations (.env templates)
log "INFO" "Initializing Environment Configuration Files..."
for example in "$ROOT"/*.example; do
  [ -f "$example" ] || continue
  target="${example%.example}"
  if [ ! -f "$target" ]; then
    cp "$example" "$target"
    log "INFO" "Created $(basename "$target") from example template"
  fi
done

# 5. Universal CLI Launcher Setup
log "INFO" "Creating Local Executable Launcher Scripts..."
cat << 'EOF' > "$ROOT/zeaz-launcher.sh"
#!/usr/bin/env bash
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export ZEAZ_HOME="$ROOT"
cd "$ROOT"
if [ -f "$ROOT/.venv/bin/python" ]; then
  exec "$ROOT/.venv/bin/python" -m app "$@"
else
  exec python3 -m app "$@"
fi
EOF
chmod +x "$ROOT/zeaz-launcher.sh"

log "SUCCESS" "=========================================================="
log "SUCCESS" "  ZEAZ Platform Setup Completed Successfully!             "
log "SUCCESS" "=========================================================="
log "INFO" "To run ZEAZ Platform, execute: ./zeaz-launcher.sh"
