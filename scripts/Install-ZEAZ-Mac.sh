#!/usr/bin/env bash
# macOS & Linux Automated Installer for ZEAZ Platform
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo "=========================================================="
echo "    ZEAZ Cross-Platform Installer (macOS & Linux)        "
echo "=========================================================="

command -v node >/dev/null || { echo "Node.js v18+ is required"; exit 1; }
command -v npm >/dev/null || { echo "NPM is required"; exit 1; }
command -v python3 >/dev/null || { echo "Python 3.11+ is required"; exit 1; }

cd "$ROOT"
echo "[INFO] Installing dependencies..."
npm install

echo "[INFO] Compiling workspaces..."
npm run build

echo "[SUCCESS] ZEAZ Platform cross-platform build completed!"
