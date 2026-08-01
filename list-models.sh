#!/usr/bin/env bash

set -Eeuo pipefail

PROGRAM_NAME="${0##*/}"
VERSION="2.0.0"

usage() {
  cat <<'USAGE'
List models from an OpenAI-compatible API.

Usage:
  list-models.sh --base-url URL --api-key KEY [options]

Required (or environment variables):
  --base-url URL          API base URL
  --api-key KEY           Provider API key

Environment variables:
  OPENAI_BASE_URL         Alternative to --base-url
  OPENAI_API_KEY          Alternative to --api-key

Output options:
  --all                   Print one model ID per line (default)
  --csv                   Print comma-separated model IDs
  --qwen                  Print quoted comma-separated value:
                          "model-id-1,model-id-2"
  --json                  Print JSON array
  --raw                   Print the original API response

Filtering options:
  --free                  Print models detected as free
  --free-mode MODE        strict | accessible

                          strict:
                            Only models explicitly identified as free by
                            model ID, pricing metadata, or provider metadata.

                          accessible:
                            If no explicit free markers are present, return
                            every model visible to the API key. Useful for
                            providers whose free-tier status is account-level
                            and not included in /models metadata.

                          Default: strict

Request options:
  --models-url URL        Override the exact models endpoint
  --header VALUE          Add an HTTP header; may be repeated
  --timeout SECONDS       Request timeout (default: 30)
  --connect-timeout SEC   Connection timeout (default: 10)
  --retries COUNT         Retry count (default: 2)
  --insecure              Disable TLS certificate verification
  --debug                 Print diagnostics to stderr
  -h, --help              Show this help
  --version               Show version

Examples:
  # OpenRouter explicit free models
  ./list-models.sh \
    --base-url https://openrouter.ai/api/v1 \
    --api-key "$OPENROUTER_API_KEY" \
    --free \
    --qwen

  # NVIDIA/Groq free-tier account fallback
  ./list-models.sh \
    --base-url https://integrate.api.nvidia.com/v1 \
    --api-key "$NVIDIA_API_KEY" \
    --free \
    --free-mode accessible \
    --qwen

  # Local Ollama; API key can be any non-empty value
  ./list-models.sh \
    --base-url http://localhost:11434/v1 \
    --api-key local \
    --json
USAGE
}

log() {
  printf '%s\n' "$*" >&2
}

debug() {
  if [[ "$DEBUG" == "true" ]]; then
    printf '[debug] %s\n' "$*" >&2
  fi
}

die() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

require_command() {
  command -v "$1" >/dev/null 2>&1 || die "Required command not found: $1"
}

is_non_negative_integer() {
  [[ "$1" =~ ^[0-9]+$ ]]
}

BASE_URL="${OPENAI_BASE_URL:-}"
API_KEY="${OPENAI_API_KEY:-}"
MODELS_URL=""
OUTPUT_MODE="all"
FREE_ONLY="false"
FREE_MODE="strict"
RAW_OUTPUT="false"
TIMEOUT="30"
CONNECT_TIMEOUT="10"
RETRIES="2"
INSECURE="false"
DEBUG="false"
EXTRA_HEADERS=()

while (($# > 0)); do
  case "$1" in
    --base-url)
      (($# >= 2)) || die "--base-url requires a value"
      BASE_URL="$2"
      shift 2
      ;;
    --api-key)
      (($# >= 2)) || die "--api-key requires a value"
      API_KEY="$2"
      shift 2
      ;;
    --models-url)
      (($# >= 2)) || die "--models-url requires a value"
      MODELS_URL="$2"
      shift 2
      ;;
    --all)
      OUTPUT_MODE="all"
      shift
      ;;
    --csv)
      OUTPUT_MODE="csv"
      shift
      ;;
    --qwen)
      OUTPUT_MODE="qwen"
      shift
      ;;
    --json)
      OUTPUT_MODE="json"
      shift
      ;;
    --raw)
      RAW_OUTPUT="true"
      shift
      ;;
    --free)
      FREE_ONLY="true"
      shift
      ;;
    --free-mode)
      (($# >= 2)) || die "--free-mode requires strict or accessible"
      FREE_MODE="$2"
      shift 2
      ;;
    --header)
      (($# >= 2)) || die "--header requires a value"
      EXTRA_HEADERS+=("$2")
      shift 2
      ;;
    --timeout)
      (($# >= 2)) || die "--timeout requires a value"
      TIMEOUT="$2"
      shift 2
      ;;
    --connect-timeout)
      (($# >= 2)) || die "--connect-timeout requires a value"
      CONNECT_TIMEOUT="$2"
      shift 2
      ;;
    --retries)
      (($# >= 2)) || die "--retries requires a value"
      RETRIES="$2"
      shift 2
      ;;
    --insecure)
      INSECURE="true"
      shift
      ;;
    --debug)
      DEBUG="true"
      shift
      ;;
    --version)
      printf '%s %s\n' "$PROGRAM_NAME" "$VERSION"
      exit 0
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    --)
      shift
      break
      ;;
    *)
      die "Unknown argument: $1"
      ;;
  esac
done

require_command curl
require_command jq

[[ -n "$BASE_URL" || -n "$MODELS_URL" ]] || \
  die "Missing --base-url/OPENAI_BASE_URL or --models-url"

[[ -n "$API_KEY" ]] || \
  die "Missing --api-key or OPENAI_API_KEY"

case "$FREE_MODE" in
  strict|accessible) ;;
  *) die "--free-mode must be strict or accessible" ;;
esac

is_non_negative_integer "$TIMEOUT" || die "--timeout must be a non-negative integer"
is_non_negative_integer "$CONNECT_TIMEOUT" || die "--connect-timeout must be a non-negative integer"
is_non_negative_integer "$RETRIES" || die "--retries must be a non-negative integer"

if [[ -z "$MODELS_URL" ]]; then
  BASE_URL="${BASE_URL%/}"

  case "$BASE_URL" in
    */models)
      MODELS_URL="$BASE_URL"
      ;;
    */v1|*/openai/v1|*/inference/v1)
      MODELS_URL="${BASE_URL}/models"
      ;;
    *)
      MODELS_URL="${BASE_URL}/v1/models"
      ;;
  esac
fi

debug "models URL: $MODELS_URL"
debug "output mode: $OUTPUT_MODE"
debug "free only: $FREE_ONLY"
debug "free mode: $FREE_MODE"

RESPONSE_FILE="$(mktemp)"
ERROR_FILE="$(mktemp)"
trap 'rm -f "$RESPONSE_FILE" "$ERROR_FILE"' EXIT

CURL_ARGS=(
  --silent
  --show-error
  --location
  --connect-timeout "$CONNECT_TIMEOUT"
  --max-time "$TIMEOUT"
  --retry "$RETRIES"
  --retry-delay 1
  --retry-connrefused
  --header "Authorization: Bearer ${API_KEY}"
  --header "Accept: application/json"
  --output "$RESPONSE_FILE"
  --write-out '%{http_code}'
)

if [[ "$INSECURE" == "true" ]]; then
  CURL_ARGS+=(--insecure)
fi

for header in "${EXTRA_HEADERS[@]}"; do
  CURL_ARGS+=(--header "$header")
done

set +e
HTTP_CODE="$(curl "${CURL_ARGS[@]}" "$MODELS_URL" 2>"$ERROR_FILE")"
CURL_STATUS=$?
set -e

if ((CURL_STATUS != 0)); then
  [[ -s "$ERROR_FILE" ]] && cat "$ERROR_FILE" >&2
  [[ -s "$RESPONSE_FILE" ]] && cat "$RESPONSE_FILE" >&2
  die "Request failed for $MODELS_URL"
fi

if [[ ! "$HTTP_CODE" =~ ^2[0-9][0-9]$ ]]; then
  [[ -s "$RESPONSE_FILE" ]] && cat "$RESPONSE_FILE" >&2
  die "API returned HTTP $HTTP_CODE"
fi

jq empty "$RESPONSE_FILE" >/dev/null 2>&1 || {
  cat "$RESPONSE_FILE" >&2 || true
  die "Provider did not return valid JSON"
}

if [[ "$RAW_OUTPUT" == "true" ]]; then
  jq . "$RESPONSE_FILE"
  exit 0
fi

# Normalize common response formats:
#   {"data":[...]}
#   {"models":[...]}
#   {"items":[...]}
#   [...]
#
# Free detection supports:
#   model IDs ending with :free
#   openrouter/free
#   pricing fields with numeric/string zero values
#   free/is_free/free_tier flags
#   tier/access/plan values containing "free"
#   metadata.free / metadata.is_free / metadata.tier
JQ_PROGRAM='def models:
  if (.data? | type) == "array" then .data
  elif (.models? | type) == "array" then .models
  elif (.items? | type) == "array" then .items
  elif type == "array" then .
  else []
  end;

def model_id:
  (.id // .model // .model_id // .name // empty)
  | select(type == "string" and length > 0);

def zero_value:
  if . == null then false
  elif type == "number" then . == 0
  elif type == "string" then
    (ascii_downcase | gsub("[[:space:]]"; "")) as $v
    | ($v == "0"
       or $v == "0.0"
       or $v == "0.00"
       or $v == "0.000000"
       or $v == "$0"
       or $v == "free")
  else false
  end;

def explicit_free_flag:
  (.free? == true)
  or (.is_free? == true)
  or (.free_tier? == true)
  or (.metadata?.free? == true)
  or (.metadata?.is_free? == true)
  or (((.tier? // .access? // .plan? // .metadata?.tier? // "") | tostring | ascii_downcase) == "free");

def free_by_id:
  (model_id | ascii_downcase) as $id
  | ($id == "openrouter/free"
     or ($id | endswith(":free"))
     or ($id | test("(^|[/_-])free($|[/_:-])")));

def pricing_values:
  if (.pricing? | type) == "object" then
    [
      .pricing.prompt?,
      .pricing.completion?,
      .pricing.input?,
      .pricing.output?,
      .pricing.request?,
      .pricing.image?,
      .pricing.audio?,
      .pricing.video?,
      .pricing.web_search?,
      .pricing.internal_reasoning?,
      .pricing.input_cache_read?,
      .pricing.input_cache_write?
    ] | map(select(. != null))
  elif (.price? | type) == "object" then
    [
      .price.prompt?,
      .price.completion?,
      .price.input?,
      .price.output?,
      .price.request?
    ] | map(select(. != null))
  else []
  end;

def free_by_pricing:
  (pricing_values) as $prices
  | (($prices | length) > 0 and ($prices | all(zero_value)));

def explicitly_free:
  free_by_id or free_by_pricing or explicit_free_flag;

models
| map(select(model_id != null))
| map({
    id: model_id,
    explicitly_free: explicitly_free
  })
| unique_by(.id)
| sort_by(.id)
'

NORMALIZED_JSON="$(jq "$JQ_PROGRAM" "$RESPONSE_FILE")"
TOTAL_COUNT="$(jq 'length' <<<"$NORMALIZED_JSON")"

if [[ "$TOTAL_COUNT" == "0" ]]; then
  debug "response shape preview:"
  if [[ "$DEBUG" == "true" ]]; then
    jq 'if type == "object" then keys else type end' "$RESPONSE_FILE" >&2
  fi
  die "No model IDs were found in the API response"
fi

RESULT_JSON="$NORMALIZED_JSON"

if [[ "$FREE_ONLY" == "true" ]]; then
  EXPLICIT_FREE_JSON="$(jq '[.[] | select(.explicitly_free)]' <<<"$NORMALIZED_JSON")"
  EXPLICIT_FREE_COUNT="$(jq 'length' <<<"$EXPLICIT_FREE_JSON")"

  if ((EXPLICIT_FREE_COUNT > 0)); then
    RESULT_JSON="$EXPLICIT_FREE_JSON"
    debug "found $EXPLICIT_FREE_COUNT explicitly free models"
  elif [[ "$FREE_MODE" == "accessible" ]]; then
    RESULT_JSON="$NORMALIZED_JSON"
    log "WARNING: Provider returned no explicit free/pricing metadata; returning all $TOTAL_COUNT models accessible to this API key."
  else
    log "WARNING: No explicitly free models were detected."
    log "The provider may not expose pricing or free-tier metadata in /models."
    log "Retry with: --free --free-mode accessible"
    RESULT_JSON='[]'
  fi
fi

IDS_JSON="$(jq '[.[].id] | unique | sort' <<<"$RESULT_JSON")"

case "$OUTPUT_MODE" in
  all)
    jq -r '.[]' <<<"$IDS_JSON"
    ;;
  csv)
    jq -r 'join(",")' <<<"$IDS_JSON"
    ;;
  qwen)
    jq -r 'join(",") | @json' <<<"$IDS_JSON"
    ;;
  json)
    jq . <<<"$IDS_JSON"
    ;;
  *)
    die "Unsupported output mode: $OUTPUT_MODE"
    ;;
esac
