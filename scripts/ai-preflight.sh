#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STRICT=false
SMOKE=false
for argument in "$@"; do
    case "$argument" in
        --strict) STRICT=true ;;
        --smoke) SMOKE=true ;;
        *) echo "Usage: $0 [--strict] [--smoke]" >&2; exit 2 ;;
    esac
done
[[ -f "$ROOT/.env.ai" ]] || { echo "Missing $ROOT/.env.ai; copy .env.ai.example first." >&2; exit 1; }
[[ -f "$ROOT/.env.production" ]] && source "$ROOT/.env.production"
source "$ROOT/.env.ai"
export AI_PROVIDER_KEYS_JSON HF_ENABLED HF_TOKEN HF_ROUTER_BASE_URL AI_MODEL_CATALOG_TTL HF_MODEL_CATALOG_TTL ZEAZ_AI_GATEWAY_URL AI_GATEWAY_PROVIDER_TOKEN
cd "$ROOT"
STRICT="$STRICT" SMOKE="$SMOKE" python3 - <<'PY'
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
if os.environ.get("SMOKE") == "true":
    from app import ai_chat
    providers=sorted({model["provider"] for model in catalog["models"] if model.get("free")})
    for provider in providers:
        model=next(item for item in catalog["models"] if item["provider"] == provider and item.get("free"))
        result=ai_chat(model["id"], "Reply with exactly: ok", max_tokens=256, temperature=0)
        if not result.get("content"):
            raise SystemExit(f"{provider} free-model smoke test returned no text")
        print(f"{provider}: free-model inference smoke test passed")
PY
