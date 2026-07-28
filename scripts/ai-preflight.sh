#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STRICT=false
[[ "${1:-}" == "--strict" ]] && STRICT=true
[[ -f "$ROOT/.env.ai" ]] || { echo "Missing $ROOT/.env.ai; copy .env.ai.example first." >&2; exit 1; }
[[ -f "$ROOT/.env.production" ]] && source "$ROOT/.env.production"
source "$ROOT/.env.ai"
export AI_PROVIDER_KEYS_JSON HF_ENABLED HF_TOKEN HF_ROUTER_BASE_URL AI_MODEL_CATALOG_TTL HF_MODEL_CATALOG_TTL
cd "$ROOT"
STRICT="$STRICT" python3 - <<'PY'
import os
from app import ai_catalog
catalog=ai_catalog()
failed=[]
for provider, state in sorted(catalog["providers"].items()):
    if state.get("enabled"):
        free=sum(1 for model in catalog["models"] if model["provider"] == provider and model.get("free"))
        suffix=f" ({free} provider-declared free)" if free else ""
        print(f"{provider}: {state['models']} live catalog models{suffix}")
    elif state.get("error"):
        print(f"{provider}: unavailable ({state['error']})")
        failed.append(provider)
print(f"AI catalog preflight passed: {len(catalog['models'])} models total.")
if os.environ.get("STRICT") == "true" and failed:
    raise SystemExit("Strict preflight failed: " + ", ".join(failed))
PY
