#!/usr/bin/env bash
# fix-codex-namespace.sh
#
# Fixes OpenAI Responses API / Codex-compatible provider errors such as:
#   Unknown parameter: 'input[526].namespace'
#
# The script removes an invalid "namespace" member only when it appears inside
# an object contained by a Responses API "input" array. It supports:
#   - JSON
#   - JSONL / NDJSON
#   - JavaScript / TypeScript object literals (token-aware conservative rewrite)
#   - Codex state/cache directories
#   - dry-run, backup, report, validation, rollback
#
# Requirements:
#   bash 3.2+, python3 3.9+
#
# Safe default:
#   ./fix-codex-namespace.sh --dry-run
#
# Apply:
#   ./fix-codex-namespace.sh --apply
#
# Scan a repository and Codex home:
#   ./fix-codex-namespace.sh --apply --root . --include-codex-home
#
# Roll back the latest run:
#   ./fix-codex-namespace.sh --rollback
#
set -Eeuo pipefail
IFS=$'\n\t'

PROGRAM="${0##*/}"
VERSION="1.0.0"

MODE="dry-run"
ROOT="."
INCLUDE_CODEX_HOME=0
BACKUP_DIR=""
REPORT_FILE=""
ROLLBACK_DIR=""
VERBOSE=0
STRICT=0
MAX_FILE_SIZE=$((20 * 1024 * 1024))

declare -a EXTRA_PATHS=()
declare -a EXCLUDES=(
  ".git"
  "node_modules"
  ".venv"
  "venv"
  "dist"
  "build"
  ".next"
  ".turbo"
  "coverage"
  "__pycache__"
)

if [[ -t 1 ]]; then
  C_RESET=$'\033[0m'
  C_RED=$'\033[31m'
  C_GREEN=$'\033[32m'
  C_YELLOW=$'\033[33m'
  C_BLUE=$'\033[34m'
  C_BOLD=$'\033[1m'
else
  C_RESET=""
  C_RED=""
  C_GREEN=""
  C_YELLOW=""
  C_BLUE=""
  C_BOLD=""
fi

log()  { printf '%s[%s]%s %s\n' "$C_BLUE" "INFO" "$C_RESET" "$*"; }
ok()   { printf '%s[%s]%s %s\n' "$C_GREEN" " OK " "$C_RESET" "$*"; }
warn() { printf '%s[%s]%s %s\n' "$C_YELLOW" "WARN" "$C_RESET" "$*" >&2; }
die()  { printf '%s[%s]%s %s\n' "$C_RED" "FAIL" "$C_RESET" "$*" >&2; exit 1; }
debug(){ (( VERBOSE )) && printf '[DEBUG] %s\n' "$*" >&2 || true; }

usage() {
  cat <<'EOF'
Usage:
  fix-codex-namespace.sh [options]

Modes:
  --dry-run                 Scan and report only (default)
  --apply                   Modify files after creating backups
  --rollback [BACKUP_DIR]   Restore files from a previous backup directory

Targets:
  --root PATH               Repository/project root (default: current directory)
  --path PATH               Additional file or directory; repeatable
  --include-codex-home      Also scan ~/.codex and common Codex state paths
  --exclude NAME            Exclude directory name; repeatable

Safety:
  --backup-dir PATH         Backup destination
  --max-file-size BYTES     Skip larger files (default: 20971520)
  --strict                  Exit nonzero if suspicious unfixable matches remain
  --report PATH             Write Markdown report
  --verbose                 Detailed logging
  -h, --help                Show help
  -V, --version             Show version

Examples:
  ./fix-codex-namespace.sh --dry-run --root .
  ./fix-codex-namespace.sh --apply --root . --include-codex-home
  ./fix-codex-namespace.sh --rollback .codex-namespace-backups/20260729T020000Z
EOF
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "Required command not found: $1"
}

abspath() {
  python3 - "$1" <<'PY'
import os, sys
print(os.path.abspath(os.path.expanduser(sys.argv[1])))
PY
}

timestamp() {
  date -u '+%Y%m%dT%H%M%SZ'
}

while (($#)); do
  case "$1" in
    --dry-run) MODE="dry-run"; shift ;;
    --apply) MODE="apply"; shift ;;
    --rollback)
      MODE="rollback"
      if (($# >= 2)) && [[ "${2:-}" != --* ]]; then
        ROLLBACK_DIR="$2"
        shift 2
      else
        shift
      fi
      ;;
    --root) [[ $# -ge 2 ]] || die "--root requires a path"; ROOT="$2"; shift 2 ;;
    --path) [[ $# -ge 2 ]] || die "--path requires a path"; EXTRA_PATHS+=("$2"); shift 2 ;;
    --include-codex-home) INCLUDE_CODEX_HOME=1; shift ;;
    --exclude) [[ $# -ge 2 ]] || die "--exclude requires a name"; EXCLUDES+=("$2"); shift 2 ;;
    --backup-dir) [[ $# -ge 2 ]] || die "--backup-dir requires a path"; BACKUP_DIR="$2"; shift 2 ;;
    --report) [[ $# -ge 2 ]] || die "--report requires a path"; REPORT_FILE="$2"; shift 2 ;;
    --max-file-size) [[ $# -ge 2 ]] || die "--max-file-size requires bytes"; MAX_FILE_SIZE="$2"; shift 2 ;;
    --strict) STRICT=1; shift ;;
    --verbose) VERBOSE=1; shift ;;
    -h|--help) usage; exit 0 ;;
    -V|--version) printf '%s %s\n' "$PROGRAM" "$VERSION"; exit 0 ;;
    *) die "Unknown argument: $1" ;;
  esac
done

require_cmd python3

ROOT="$(abspath "$ROOT")"
[[ -e "$ROOT" ]] || die "Root does not exist: $ROOT"

RUN_ID="$(timestamp)"
if [[ -z "$BACKUP_DIR" ]]; then
  BACKUP_DIR="$ROOT/.codex-namespace-backups/$RUN_ID"
fi
BACKUP_DIR="$(abspath "$BACKUP_DIR")"

if [[ -z "$REPORT_FILE" ]]; then
  REPORT_FILE="$ROOT/codex-namespace-fix-report-$RUN_ID.md"
fi
REPORT_FILE="$(abspath "$REPORT_FILE")"

restore_backup() {
  local backup="$1"
  [[ -d "$backup" ]] || die "Backup directory not found: $backup"
  [[ -f "$backup/manifest.tsv" ]] || die "Missing backup manifest: $backup/manifest.tsv"

  log "Restoring files from $backup"
  local restored=0
  while IFS=$'\t' read -r original relative sha_before; do
    [[ "$original" == "original_path" ]] && continue
    [[ -n "$original" && -n "$relative" ]] || continue
    local source="$backup/files/$relative"
    [[ -f "$source" ]] || {
      warn "Backup file missing: $source"
      continue
    }
    mkdir -p "$(dirname "$original")"
    cp -p "$source" "$original"
    restored=$((restored + 1))
    debug "Restored $original"
  done < "$backup/manifest.tsv"
  ok "Restored $restored file(s)"
}

if [[ "$MODE" == "rollback" ]]; then
  if [[ -z "$ROLLBACK_DIR" ]]; then
    base="$ROOT/.codex-namespace-backups"
    [[ -d "$base" ]] || die "No backup directory found: $base"
    ROLLBACK_DIR="$(find "$base" -mindepth 1 -maxdepth 1 -type d | sort | tail -n 1)"
    [[ -n "$ROLLBACK_DIR" ]] || die "No backup run found under $base"
  fi
  restore_backup "$(abspath "$ROLLBACK_DIR")"
  exit 0
fi

declare -a TARGETS=("$ROOT")
for p in "${EXTRA_PATHS[@]}"; do
  TARGETS+=("$(abspath "$p")")
done

if (( INCLUDE_CODEX_HOME )); then
  for p in \
    "${CODEX_HOME:-$HOME/.codex}" \
    "$HOME/.config/codex" \
    "$HOME/Library/Application Support/Codex"; do
    [[ -e "$p" ]] && TARGETS+=("$(abspath "$p")")
  done
fi

EXCLUDES_JOINED=""
for item in "${EXCLUDES[@]}"; do
  [[ -n "$EXCLUDES_JOINED" ]] && EXCLUDES_JOINED+=$'\x1f'
  EXCLUDES_JOINED+="$item"
done

WORK_DIR="$(mktemp -d "${TMPDIR:-/tmp}/fix-codex-namespace.XXXXXX")"
trap 'rm -rf "$WORK_DIR"' EXIT

RESULTS_JSONL="$WORK_DIR/results.jsonl"
FILES_LIST="$WORK_DIR/files.bin"
: > "$RESULTS_JSONL"
: > "$FILES_LIST"

log "Mode: $MODE"
log "Root: $ROOT"
(( INCLUDE_CODEX_HOME )) && log "Codex home scanning enabled"

python3 - "$FILES_LIST" "$MAX_FILE_SIZE" "$EXCLUDES_JOINED" "${TARGETS[@]}" <<'PY'
import os, sys

out_path = sys.argv[1]
max_size = int(sys.argv[2])
excludes = set(filter(None, sys.argv[3].split("\x1f")))
targets = sys.argv[4:]

extensions = {
    ".json", ".jsonl", ".ndjson",
    ".js", ".jsx", ".mjs", ".cjs",
    ".ts", ".tsx", ".mts", ".cts",
}
specific_names = {
    "config", "settings", "state", "session", "history",
}

seen = set()
with open(out_path, "wb") as out:
    for target in targets:
        target = os.path.abspath(os.path.expanduser(target))
        if not os.path.exists(target):
            continue

        candidates = []
        if os.path.isfile(target):
            candidates = [target]
        else:
            for root, dirs, files in os.walk(target):
                dirs[:] = [
                    d for d in dirs
                    if d not in excludes and not d.startswith(".codex-namespace-backups")
                ]
                for name in files:
                    path = os.path.join(root, name)
                    ext = os.path.splitext(name)[1].lower()
                    stem = os.path.splitext(name)[0].lower()
                    if ext in extensions or stem in specific_names:
                        candidates.append(path)

        for path in candidates:
            real = os.path.realpath(path)
            if real in seen:
                continue
            seen.add(real)
            try:
                st = os.stat(path)
            except OSError:
                continue
            if not os.path.isfile(path) or st.st_size > max_size:
                continue
            out.write(path.encode("utf-8", "surrogateescape") + b"\0")
PY

PY_FIXER="$WORK_DIR/fixer.py"
cat > "$PY_FIXER" <<'PY'
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

path = Path(sys.argv[1])
mode = sys.argv[2]
backup_dir = Path(sys.argv[3])
root = Path(sys.argv[4])

def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def remove_namespace_from_input(value: Any) -> tuple[Any, int]:
    """
    Recursively traverses JSON. A namespace key is removed only from dicts that
    are direct elements of a list stored under key "input".
    """
    removed = 0

    def walk(node: Any, parent_key: str | None = None) -> Any:
        nonlocal removed
        if isinstance(node, dict):
            out = {}
            for k, v in node.items():
                if parent_key == "input" and k == "namespace":
                    removed += 1
                    continue
                out[k] = walk(v, k)
            return out
        if isinstance(node, list):
            return [walk(item, parent_key) for item in node]
        return node

    return walk(value), removed

def fix_json(text: str) -> tuple[str, int, str]:
    data = json.loads(text)
    fixed, count = remove_namespace_from_input(data)
    if count == 0:
        return text, 0, "json"
    indent = 2
    trailing_nl = "\n" if text.endswith("\n") else ""
    return json.dumps(fixed, ensure_ascii=False, indent=indent) + trailing_nl, count, "json"

def fix_jsonl(text: str) -> tuple[str, int, str]:
    lines = text.splitlines(keepends=True)
    out = []
    total = 0
    parsed = 0
    for line in lines:
        ending = "\n" if line.endswith("\n") else ""
        raw = line[:-1] if ending else line
        if not raw.strip():
            out.append(line)
            continue
        obj = json.loads(raw)
        fixed, count = remove_namespace_from_input(obj)
        total += count
        parsed += 1
        if count:
            out.append(json.dumps(fixed, ensure_ascii=False, separators=(",", ":")) + ending)
        else:
            out.append(line)
    if parsed == 0:
        raise ValueError("no JSONL records")
    return "".join(out), total, "jsonl"

@dataclass
class Token:
    kind: str
    start: int
    end: int
    text: str

IDENT_START = re.compile(r"[A-Za-z_$]")
IDENT_CONT = re.compile(r"[A-Za-z0-9_$]")

def tokenize_js(src: str) -> list[Token]:
    """
    Minimal JavaScript/TypeScript lexer. It skips comments, strings, templates,
    and regex literals conservatively, while exposing punctuation and identifiers.
    It is intentionally not a full parser.
    """
    tokens: list[Token] = []
    n = len(src)
    i = 0
    prev_sig = ""

    def regex_can_start(prev: str) -> bool:
        return prev in {"", "(", "[", "{", "=", ":", ",", "!", "?", ";", "return", "=>", "case"}

    while i < n:
        c = src[i]
        if c.isspace():
            i += 1
            continue

        if c == "/" and i + 1 < n and src[i + 1] == "/":
            j = src.find("\n", i + 2)
            i = n if j < 0 else j + 1
            continue

        if c == "/" and i + 1 < n and src[i + 1] == "*":
            j = src.find("*/", i + 2)
            i = n if j < 0 else j + 2
            continue

        if c in ("'", '"'):
            quote = c
            j = i + 1
            while j < n:
                if src[j] == "\\":
                    j += 2
                    continue
                if src[j] == quote:
                    j += 1
                    break
                j += 1
            tokens.append(Token("string", i, j, src[i:j]))
            prev_sig = "string"
            i = j
            continue

        if c == "`":
            j = i + 1
            depth = 0
            while j < n:
                if src[j] == "\\":
                    j += 2
                    continue
                if src.startswith("${", j):
                    depth += 1
                    j += 2
                    continue
                if src[j] == "}" and depth:
                    depth -= 1
                    j += 1
                    continue
                if src[j] == "`" and depth == 0:
                    j += 1
                    break
                j += 1
            tokens.append(Token("template", i, j, src[i:j]))
            prev_sig = "template"
            i = j
            continue

        if c == "/" and regex_can_start(prev_sig):
            j = i + 1
            in_class = False
            while j < n:
                if src[j] == "\\":
                    j += 2
                    continue
                if src[j] == "[":
                    in_class = True
                elif src[j] == "]":
                    in_class = False
                elif src[j] == "/" and not in_class:
                    j += 1
                    while j < n and src[j].isalpha():
                        j += 1
                    break
                elif src[j] == "\n":
                    break
                j += 1
            tokens.append(Token("regex", i, j, src[i:j]))
            prev_sig = "regex"
            i = j
            continue

        if IDENT_START.match(c):
            j = i + 1
            while j < n and IDENT_CONT.match(src[j]):
                j += 1
            text = src[i:j]
            tokens.append(Token("ident", i, j, text))
            prev_sig = text
            i = j
            continue

        if c.isdigit():
            j = i + 1
            while j < n and (src[j].isalnum() or src[j] in "._"):
                j += 1
            tokens.append(Token("number", i, j, src[i:j]))
            prev_sig = "number"
            i = j
            continue

        if src.startswith("=>", i):
            tokens.append(Token("punct", i, i + 2, "=>"))
            prev_sig = "=>"
            i += 2
            continue

        tokens.append(Token("punct", i, i + 1, c))
        prev_sig = c
        i += 1

    return tokens

def matching_pairs(tokens: list[Token]) -> tuple[dict[int, int], dict[int, int]]:
    opens = {"{": "}", "[": "]", "(": ")"}
    closes = {v: k for k, v in opens.items()}
    stack: list[tuple[str, int]] = []
    forward: dict[int, int] = {}
    backward: dict[int, int] = {}
    for idx, tok in enumerate(tokens):
        if tok.text in opens:
            stack.append((tok.text, idx))
        elif tok.text in closes:
            if stack and stack[-1][0] == closes[tok.text]:
                _, start = stack.pop()
                forward[start] = idx
                backward[idx] = start
    return forward, backward

def key_name(tok: Token) -> str | None:
    if tok.kind == "ident":
        return tok.text
    if tok.kind == "string" and len(tok.text) >= 2:
        quote = tok.text[0]
        if tok.text[-1] == quote:
            try:
                return json.loads(tok.text) if quote == '"' else tok.text[1:-1]
            except Exception:
                return tok.text[1:-1]
    return None

def fix_js_source(src: str) -> tuple[str, int, str]:
    """
    Removes namespace properties only from object literals that are direct
    elements of an array assigned to an "input" property.

    Supported pattern:
      { input: [ { namespace: "...", role: "user", ... } ] }

    It does not rewrite computed keys, spreads, or ambiguous syntax.
    """
    tokens = tokenize_js(src)
    forward, _ = matching_pairs(tokens)
    removals: list[tuple[int, int]] = []

    input_arrays: list[tuple[int, int]] = []
    for i in range(len(tokens) - 2):
        if key_name(tokens[i]) != "input":
            continue
        if tokens[i + 1].text != ":" or tokens[i + 2].text != "[":
            continue
        end = forward.get(i + 2)
        if end is not None:
            input_arrays.append((i + 2, end))

    for arr_start, arr_end in input_arrays:
        depth = 0
        i = arr_start + 1
        while i < arr_end:
            tok = tokens[i]
            if tok.text in "[({":
                if tok.text == "{" and depth == 0:
                    obj_end = forward.get(i)
                    if obj_end is None or obj_end > arr_end:
                        i += 1
                        continue
                    j = i + 1
                    member_depth = 0
                    while j < obj_end:
                        t = tokens[j]
                        if t.text in "[({":
                            member_depth += 1
                            j += 1
                            continue
                        if t.text in "])}":
                            member_depth -= 1
                            j += 1
                            continue

                        if member_depth == 0 and key_name(t) == "namespace":
                            if j + 1 < obj_end and tokens[j + 1].text == ":":
                                value_start = j + 2
                                k = value_start
                                value_depth = 0
                                while k < obj_end:
                                    kt = tokens[k]
                                    if kt.text in "[({":
                                        value_depth += 1
                                    elif kt.text in "])}":
                                        if value_depth > 0:
                                            value_depth -= 1
                                    elif kt.text == "," and value_depth == 0:
                                        break
                                    k += 1

                                start_pos = t.start
                                end_pos = tokens[k].end if k < obj_end and tokens[k].text == "," else (
                                    tokens[k - 1].end if k > value_start else tokens[j + 1].end
                                )

                                # If this is the final property, consume a preceding comma.
                                if k >= obj_end:
                                    p = j - 1
                                    if p > i and tokens[p].text == ",":
                                        start_pos = tokens[p].start

                                removals.append((start_pos, end_pos))
                                j = max(k + 1, j + 2)
                                continue
                        j += 1
                    i = obj_end + 1
                    continue
                depth += 1
            elif tok.text in "])}":
                depth = max(0, depth - 1)
            i += 1

    if not removals:
        return src, 0, "javascript"

    # Merge overlaps and apply from right to left.
    merged: list[tuple[int, int]] = []
    for start, end in sorted(removals):
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))

    out = src
    for start, end in reversed(merged):
        out = out[:start] + out[end:]
    return out, len(merged), "javascript"

raw = path.read_bytes()
before_sha = sha256(raw)

try:
    text = raw.decode("utf-8")
except UnicodeDecodeError:
    print(json.dumps({
        "path": str(path), "status": "skipped", "reason": "non-utf8",
        "changes": 0, "before_sha": before_sha
    }))
    raise SystemExit(0)

suffix = path.suffix.lower()
attempts = []
if suffix == ".json":
    attempts = [fix_json]
elif suffix in {".jsonl", ".ndjson"}:
    attempts = [fix_jsonl]
elif suffix in {".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".mts", ".cts"}:
    attempts = [fix_js_source]
else:
    stripped = text.lstrip()
    if stripped.startswith(("{", "[")):
        attempts = [fix_json, fix_jsonl]
    else:
        attempts = [fix_js_source]

fixed = text
count = 0
kind = "unknown"
errors = []
for fn in attempts:
    try:
        candidate, n, detected = fn(text)
        if n:
            fixed, count, kind = candidate, n, detected
            break
        kind = detected
    except Exception as exc:
        errors.append(f"{fn.__name__}: {exc}")

suspicious = bool(re.search(r'(?s)\binput\s*:\s*\[.*?\bnamespace\s*:', text)) or \
             bool(re.search(r'(?s)"input"\s*:\s*\[.*?"namespace"\s*:', text))

if count == 0:
    print(json.dumps({
        "path": str(path),
        "status": "unchanged",
        "kind": kind,
        "changes": 0,
        "suspicious": suspicious,
        "errors": errors,
        "before_sha": before_sha,
    }, ensure_ascii=False))
    raise SystemExit(0)

new_raw = fixed.encode("utf-8")
after_sha = sha256(new_raw)

backup_rel = None
if mode == "apply":
    try:
        rel = path.resolve().relative_to(root.resolve())
        backup_rel = Path("root") / rel
    except ValueError:
        safe = str(path.resolve()).lstrip(os.sep).replace(":", "_")
        backup_rel = Path("external") / safe

    backup_path = backup_dir / "files" / backup_rel
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, backup_path)

    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(new_raw)
            fh.flush()
            os.fsync(fh.fileno())
        os.chmod(tmp_name, path.stat().st_mode)
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)

print(json.dumps({
    "path": str(path),
    "status": "changed" if mode == "apply" else "would-change",
    "kind": kind,
    "changes": count,
    "suspicious": False,
    "before_sha": before_sha,
    "after_sha": after_sha,
    "backup_rel": str(backup_rel) if backup_rel else None,
    "errors": errors,
}, ensure_ascii=False))
PY

if [[ "$MODE" == "apply" ]]; then
  mkdir -p "$BACKUP_DIR/files"
  printf 'original_path\trelative_backup_path\tsha256_before\n' > "$BACKUP_DIR/manifest.tsv"
fi

scanned=0
changed_files=0
changed_fields=0
suspicious_files=0
skipped=0

while IFS= read -r -d '' file; do
  scanned=$((scanned + 1))
  debug "Scanning $file"

  result="$(python3 "$PY_FIXER" "$file" "$MODE" "$BACKUP_DIR" "$ROOT")" || {
    warn "Failed to process: $file"
    skipped=$((skipped + 1))
    continue
  }
  printf '%s\n' "$result" >> "$RESULTS_JSONL"

  status="$(python3 -c 'import json,sys; print(json.load(sys.stdin).get("status",""))' <<<"$result")"
  changes="$(python3 -c 'import json,sys; print(json.load(sys.stdin).get("changes",0))' <<<"$result")"
  suspicious="$(python3 -c 'import json,sys; print(1 if json.load(sys.stdin).get("suspicious") else 0)' <<<"$result")"

  if [[ "$status" == "changed" || "$status" == "would-change" ]]; then
    changed_files=$((changed_files + 1))
    changed_fields=$((changed_fields + changes))
    printf '%s %s: removed %s invalid namespace field(s)\n' \
      "$([[ "$MODE" == "apply" ]] && printf '%s' "$C_GREEN" || printf '%s' "$C_YELLOW")" \
      "$file" "$changes"
    printf '%s' "$C_RESET"

    if [[ "$MODE" == "apply" ]]; then
      backup_rel="$(python3 -c 'import json,sys; print(json.load(sys.stdin).get("backup_rel") or "")' <<<"$result")"
      before_sha="$(python3 -c 'import json,sys; print(json.load(sys.stdin).get("before_sha") or "")' <<<"$result")"
      printf '%s\t%s\t%s\n' "$file" "$backup_rel" "$before_sha" >> "$BACKUP_DIR/manifest.tsv"
    fi
  elif [[ "$status" == "skipped" ]]; then
    skipped=$((skipped + 1))
  fi

  (( suspicious )) && suspicious_files=$((suspicious_files + 1))
done < "$FILES_LIST"

python3 - "$RESULTS_JSONL" "$REPORT_FILE" "$MODE" "$ROOT" "$BACKUP_DIR" <<'PY'
import json, sys
from datetime import datetime, timezone
from pathlib import Path

results_path = Path(sys.argv[1])
report_path = Path(sys.argv[2])
mode, root, backup = sys.argv[3:6]

rows = []
for line in results_path.read_text(encoding="utf-8").splitlines():
    if line.strip():
        rows.append(json.loads(line))

changed = [r for r in rows if r.get("status") in {"changed", "would-change"}]
suspicious = [r for r in rows if r.get("suspicious") and not r.get("changes")]
skipped = [r for r in rows if r.get("status") == "skipped"]

lines = [
    "# Codex Responses API namespace fix report",
    "",
    f"- Generated: {datetime.now(timezone.utc).isoformat()}",
    f"- Mode: `{mode}`",
    f"- Root: `{root}`",
    f"- Files scanned: **{len(rows)}**",
    f"- Files changed/would change: **{len(changed)}**",
    f"- Invalid fields removed: **{sum(int(r.get('changes', 0)) for r in changed)}**",
    f"- Suspicious unresolved files: **{len(suspicious)}**",
    f"- Skipped files: **{len(skipped)}**",
]
if mode == "apply":
    lines.append(f"- Backup: `{backup}`")

lines += ["", "## Changed files", ""]
if changed:
    lines += ["| File | Parser | Fields removed | Status |", "|---|---:|---:|---|"]
    for r in changed:
        lines.append(
            f"| `{r['path']}` | {r.get('kind','')} | {r.get('changes',0)} | {r.get('status','')} |"
        )
else:
    lines.append("No invalid `namespace` fields were found inside Responses API `input` arrays.")

if suspicious:
    lines += ["", "## Suspicious unresolved files", ""]
    for r in suspicious:
        lines.append(f"- `{r['path']}`")

report_path.parent.mkdir(parents=True, exist_ok=True)
report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
PY

printf '\n%sSummary%s\n' "$C_BOLD" "$C_RESET"
printf '  Files scanned:             %d\n' "$scanned"
printf '  Files changed/would change:%d\n' "$changed_files"
printf '  Invalid fields removed:    %d\n' "$changed_fields"
printf '  Suspicious unresolved:     %d\n' "$suspicious_files"
printf '  Skipped:                   %d\n' "$skipped"
printf '  Report:                    %s\n' "$REPORT_FILE"

if [[ "$MODE" == "apply" && "$changed_files" -gt 0 ]]; then
  printf '  Backup:                    %s\n' "$BACKUP_DIR"
  ok "Applied fix successfully"
  log "Rollback command: $PROGRAM --root \"$ROOT\" --rollback \"$BACKUP_DIR\""
elif [[ "$MODE" == "dry-run" && "$changed_files" -gt 0 ]]; then
  warn "Dry-run only. Re-run with --apply to modify files."
else
  ok "No invalid input[].namespace fields found"
fi

if (( STRICT )) && (( suspicious_files > 0 )); then
  die "Strict mode: suspicious unresolved matches remain"
fi
