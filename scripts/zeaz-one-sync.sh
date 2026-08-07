#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE_ROOT="${ZEAZ_ONE_SOURCE_ROOT:-$ROOT/apps/zeaz-one}"
RUNTIME_ROOT="${ZEAZ_ONE_RUNTIME_ROOT:-$HOME/services/zeaz-one}"
RELEASES_DIR="$RUNTIME_ROOT/releases"
CURRENT_LINK="$RUNTIME_ROOT/current"

update_repo=false
deploy_local=true
cloudflare_mode="none"
enable_www_redirect=false
status_only=false
stop_only=false

log() { printf '[zeaz-one-sync] %s\n' "$*"; }
fail() { printf '[zeaz-one-sync] ERROR: %s\n' "$*" >&2; exit 1; }

compose() {
  local release="$1"
  shift
  docker compose -f "$release/docker-compose.yml" "$@"
}

usage() {
  cat <<'USAGE'
Usage:
  ./scripts/zeaz-one-sync.sh [options]

Options:
  --update             Fast-forward the checked-out main branch from origin/main.
  --skip-local         Do not stage or deploy the bundled local services.
  --plan-cloudflare    Reconcile ZEAZ One DNS and create a reviewed Terraform plan.
  --apply-cloudflare   Reconcile ZEAZ One DNS and explicitly apply the saved plan.
  --www-redirect       Also manage www.zeaz.dev/products/zeaz-one as a Worker redirect.
  --status             Show the active local release and service status.
  --stop               Stop the active local ZEAZ One services.
  -h, --help

Examples:
  ./scripts/zeaz-one-sync.sh --update
  ./scripts/zeaz-one-sync.sh --update --plan-cloudflare
  ./scripts/zeaz-one-sync.sh --skip-local --apply-cloudflare
  ./scripts/zeaz-one-sync.sh --skip-local --plan-cloudflare --www-redirect
USAGE
}

while (($#)); do
  case "$1" in
    --update) update_repo=true ;;
    --skip-local) deploy_local=false ;;
    --plan-cloudflare)
      [[ "$cloudflare_mode" == "none" ]] || fail "Choose only one Cloudflare mode."
      cloudflare_mode="plan"
      ;;
    --apply-cloudflare)
      [[ "$cloudflare_mode" == "none" ]] || fail "Choose only one Cloudflare mode."
      cloudflare_mode="apply"
      ;;
    --www-redirect) enable_www_redirect=true ;;
    --status) status_only=true ;;
    --stop) stop_only=true ;;
    -h|--help) usage; exit 0 ;;
    *) fail "Unknown option: $1" ;;
  esac
  shift
done

if [[ "$status_only" == true || "$stop_only" == true ]]; then
  [[ "$status_only" != "$stop_only" ]] || fail "Choose only --status or --stop."
  [[ -L "$CURRENT_LINK" ]] || fail "No active ZEAZ One release at $CURRENT_LINK."
  command -v docker >/dev/null 2>&1 || fail "Docker is required."
  docker compose version >/dev/null 2>&1 || fail "Docker Compose v2 is required."
  if [[ "$status_only" == true ]]; then
    compose "$CURRENT_LINK" ps
  else
    compose "$CURRENT_LINK" down
  fi
  exit 0
fi

if [[ "$update_repo" == true ]]; then
  command -v git >/dev/null 2>&1 || fail "git is required for --update."
  [[ -d "$ROOT/.git" ]] || fail "$ROOT is not a Git working tree."
  branch="$(git -C "$ROOT" branch --show-current)"
  [[ "$branch" == "main" ]] || fail "--update requires the main branch; current branch is $branch."
  git -C "$ROOT" diff --quiet || fail "Tracked working-tree changes must be committed or stashed first."
  git -C "$ROOT" diff --cached --quiet || fail "Staged changes must be committed or stashed first."
  log "Fetching origin/main..."
  git -C "$ROOT" fetch --prune origin main
  git -C "$ROOT" merge --ff-only origin/main
fi

if [[ "$deploy_local" == true ]]; then
  command -v docker >/dev/null 2>&1 || fail "Docker is required."
  docker compose version >/dev/null 2>&1 || fail "Docker Compose v2 is required."
  command -v curl >/dev/null 2>&1 || fail "curl is required."
  [[ -f "$SOURCE_ROOT/docker-compose.yml" ]] || fail "ZEAZ One source is incomplete: $SOURCE_ROOT"
  [[ -f "$SOURCE_ROOT/api/server.mjs" ]] || fail "ZEAZ One API source is missing."
  [[ -f "$SOURCE_ROOT/public/one/index.html" ]] || fail "ZEAZ One website source is missing."
  [[ -f "$SOURCE_ROOT/public/one/product.json" ]] || fail "ZEAZ One public product source is missing."

  mkdir -p "$RUNTIME_ROOT" "$RELEASES_DIR"
  release_id="$(date -u +%Y%m%dT%H%M%SZ)"
  if command -v git >/dev/null 2>&1 && [[ -d "$ROOT/.git" ]]; then
    release_id+="-$(git -C "$ROOT" rev-parse --short=12 HEAD)"
  fi
  release="$RELEASES_DIR/$release_id"
  incoming="$(mktemp -d "$RUNTIME_ROOT/.incoming.XXXXXX")"
  previous=""
  [[ -L "$CURRENT_LINK" ]] && previous="$(readlink -f "$CURRENT_LINK")"

  cleanup() { rm -rf -- "$incoming"; }
  trap cleanup EXIT

  log "Staging source from $SOURCE_ROOT..."
  cp -a "$SOURCE_ROOT/." "$incoming/"
  mv "$incoming" "$release"
  trap - EXIT

  log "Validating Docker Compose and JavaScript..."
  compose "$release" config --quiet
  docker run --rm --read-only -v "$release/api:/app:ro" -w /app node:22-alpine node --check server.mjs

  log "Deploying release $release_id..."
  if ! compose "$release" up -d --remove-orphans --force-recreate; then
    log "Deployment failed; restoring the previous active release."
    if [[ -n "$previous" && -f "$previous/docker-compose.yml" ]]; then
      compose "$previous" up -d --remove-orphans --force-recreate || true
    fi
    rm -rf -- "$release"
    exit 1
  fi

  healthy=false
  for _ in $(seq 1 30); do
    if curl --fail --silent http://127.0.0.1:18081/ >/dev/null \
      && curl --fail --silent http://127.0.0.1:18081/product.json >/dev/null \
      && curl --fail --silent http://127.0.0.1:18082/products/zeaz-one/ >/dev/null \
      && curl --fail --silent http://127.0.0.1:18083/zeaz-one/ >/dev/null \
      && curl --fail --silent http://127.0.0.1:18084/health >/dev/null; then
      healthy=true
      break
    fi
    sleep 2
  done
  if [[ "$healthy" != true ]]; then
    log "Health checks failed; restoring the previous active release."
    if [[ -n "$previous" && -f "$previous/docker-compose.yml" ]]; then
      compose "$previous" up -d --remove-orphans --force-recreate || true
    fi
    rm -rf -- "$release"
    exit 1
  fi

  ln -sfn "$release" "$RUNTIME_ROOT/.current-next"
  mv -Tf "$RUNTIME_ROOT/.current-next" "$CURRENT_LINK"
  log "Activated $CURRENT_LINK -> $release"

  active="$(readlink -f "$CURRENT_LINK")"
  mapfile -t releases < <(find "$RELEASES_DIR" -mindepth 1 -maxdepth 1 -type d -printf '%T@ %p\n' | sort -nr | cut -d' ' -f2-)
  kept=0
  for candidate in "${releases[@]}"; do
    [[ "$(readlink -f "$candidate")" == "$active" ]] && continue
    kept=$((kept + 1))
    if ((kept > 4)); then
      rm -rf -- "$candidate"
    fi
  done
fi

if [[ "$cloudflare_mode" != "none" ]]; then
  [[ -x "$ROOT/scripts/cloudflare-apply.sh" ]] || fail "Cloudflare apply wrapper is missing."
  export FORCE_ENABLE_ZEAZ_ONE=true
  export FORCE_ENABLE_ZEAZ_ONE_API_ROUTE=true
  if [[ "$enable_www_redirect" == true ]]; then
    export FORCE_ENABLE_ZEAZ_ONE_WWW_REDIRECT=true
  fi

  args=(--zeaz-one)
  [[ "$cloudflare_mode" == "apply" ]] && args+=(--apply)
  "$ROOT/scripts/cloudflare-apply.sh" "${args[@]}"
fi

if [[ "$deploy_local" == true ]]; then
  compose "$CURRENT_LINK" ps
fi
