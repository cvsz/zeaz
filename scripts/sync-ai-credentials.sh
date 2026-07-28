#!/usr/bin/env bash
# Copy only the AI provider credentials needed by the local live catalog.
# Values stay in ignored environment files and are never printed.
set -Eeuo pipefail

SOURCE="${1:-/home/cvsz/zeaz-provider/.env.provider}"
TARGET="${2:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/.env.ai}"

[[ -f "$SOURCE" ]] || { echo "Credential source not found." >&2; exit 1; }
[[ -f "$TARGET" ]] || { echo "AI environment file not found." >&2; exit 1; }
command -v node >/dev/null 2>&1 || { echo "Node.js is required." >&2; exit 1; }

SOURCE="$SOURCE" TARGET="$TARGET" node <<'NODE'
const fs = require("fs");
const source = fs.readFileSync(process.env.SOURCE, "utf8");
const targetPath = process.env.TARGET;
let target = fs.readFileSync(targetPath, "utf8");
const read = (text, key) => {
  const line = text.split(/\r?\n/).find((row) => row.startsWith(`${key}=`));
  return line ? line.slice(key.length + 1).trim().replace(/^['"]|['"]$/g, "") : "";
};
const values = {
  gemini: read(source, "GEMINI_API_KEY"),
  nvidia: read(source, "NVIDIA_NIM_API_KEY"),
  zai: read(source, "ZAI_API_KEY"),
  opencode: read(source, "OPENCODE_API_KEY"),
  openrouter: read(source, "OPENROUTER_API_KEY"),
  groq: read(source, "GROQ_API_KEY"),
  // ModelArk calls use ARK_API_KEY. Keep BYTEPLUS_API_KEY as a legacy alias
  // for existing vaults during migration.
  byteplus: read(source, "ARK_API_KEY") || read(target, "ARK_API_KEY") || read(source, "BYTEPLUS_API_KEY"),
  fireworks: read(source, "FIREWORKS_API_KEY"),
};
if (Object.values(values).some((value) => !value)) throw new Error("A required AI provider key is missing.");
let existing = {};
try { existing = JSON.parse(read(target, "AI_PROVIDER_KEYS_JSON") || "{}"); } catch { throw new Error("AI_PROVIDER_KEYS_JSON is invalid."); }
const merged = JSON.stringify({ ...existing, ...values });
const replacement = `AI_PROVIDER_KEYS_JSON='${merged}'`;
if (/^AI_PROVIDER_KEYS_JSON=.*/m.test(target)) target = target.replace(/^AI_PROVIDER_KEYS_JSON=.*/m, replacement);
else target += `${target.endsWith("\n") ? "" : "\n"}${replacement}\n`;
fs.writeFileSync(targetPath, target, { mode: 0o600 });
NODE

chmod 600 "$TARGET"
echo "AI provider credentials synchronized without displaying secret values."
