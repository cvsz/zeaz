#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
[[ -f "$ROOT/.env.ai" ]] || { echo "Missing $ROOT/.env.ai; copy .env.ai.example first." >&2; exit 1; }
[[ -f "$ROOT/.env.production" ]] && source "$ROOT/.env.production"
source "$ROOT/.env.ai"
export AI_PROVIDER_KEYS_JSON HF_ENABLED HF_TOKEN HF_ROUTER_BASE_URL AI_MODEL_CATALOG_TTL HF_MODEL_CATALOG_TTL
cd "$ROOT"
python3 - <<'PY'
from app import ai_catalog
catalog=ai_catalog()
for provider, state in sorted(catalog["providers"].items()):
    if state.get("enabled"):
        print(f"{provider}: {state['models']} live catalog models")
    elif state.get("error"):
        print(f"{provider}: unavailable ({state['error']})")
print(f"AI catalog preflight passed: {len(catalog['models'])} models total.")
PY
