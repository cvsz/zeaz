#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_ENV="$ROOT/.env.production"
AI_ENV="$ROOT/.env.ai"

[[ -f "$APP_ENV" ]] && source "$APP_ENV"
[[ -f "$AI_ENV" ]] || { echo "Missing $AI_ENV; copy .env.ai.example first." >&2; exit 1; }
source "$AI_ENV"

[[ "${HF_ENABLED:-false}" == "true" ]] || { echo "HF_ENABLED must be true for preflight." >&2; exit 1; }
[[ -n "${HF_TOKEN:-}" && "${HF_TOKEN}" != replace-with-* ]] || { echo "HF_TOKEN is not configured." >&2; exit 1; }
[[ "${HF_ROUTER_BASE_URL:-https://router.huggingface.co/v1}" == "https://router.huggingface.co/v1" ]] || { echo "HF_ROUTER_BASE_URL must use the official Router." >&2; exit 1; }

export HF_ENABLED HF_TOKEN HF_ROUTER_BASE_URL HF_MODEL_CATALOG_TTL
cd "$ROOT"
python3 - <<'PY'
from app import hf_chat, hf_models
models = hf_models()
if not models:
    raise SystemExit("Hugging Face Router returned no chat models for this token.")
result = hf_chat(models[0]["id"], "Reply with exactly: ok", max_tokens=8, temperature=0)
if not result["content"].strip():
    raise SystemExit("Hugging Face Router returned an empty chat response.")
print(f"Hugging Face preflight passed: {len(models)} router models available and chat inference works.")
PY
