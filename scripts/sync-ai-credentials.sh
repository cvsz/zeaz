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
const first = (...candidates) => candidates.find(Boolean) || "";
const values = {
  gemini: first(read(target, "GEMINI_API_KEY"), read(target, "GOOGLE_API_KEY"), read(source, "GEMINI_API_KEY")),
  nvidia: first(read(target, "NVIDIA_NIM_API_KEY"), read(source, "NVIDIA_NIM_API_KEY")),
  zai: first(read(target, "ZAI_API_KEY"), read(source, "ZAI_API_KEY")),
  opencode: first(read(target, "OPENCODE_API_KEY"), read(source, "OPENCODE_API_KEY")),
  openrouter: first(read(target, "OPENROUTER_API_KEY"), read(source, "OPENROUTER_API_KEY")),
  groq: first(read(target, "GROQ_API_KEY"), read(source, "GROQ_API_KEY")),
  // ModelArk calls use ARK_API_KEY. Keep BYTEPLUS_API_KEY as a legacy alias
  // for existing vaults during migration.
  byteplus: read(source, "ARK_API_KEY") || read(target, "ARK_API_KEY") || read(source, "BYTEPLUS_API_KEY"),
  fireworks: first(read(target, "FIREWORKS_API_KEY"), read(source, "FIREWORKS_API_KEY")),
  openai: first(read(target, "OPENAI_API_KEY"), read(source, "OPENAI_API_KEY")),
  kimi: first(read(target, "KIMI_API_KEY"), read(target, "MOONSHOT_API_KEY"), read(source, "KIMI_API_KEY")),
  scaleway: first(read(target, "SCALEWAY_API_KEY"), read(target, "SCW_SECRET_KEY"), read(source, "SCALEWAY_API_KEY")),
  together: first(read(target, "TOGETHER_API_KEY"), read(source, "TOGETHER_API_KEY")),
  github: first(read(target, "GITHUB_MODELS_TOKEN"), read(source, "GITHUB_MODELS_TOKEN"), read(source, "GH_MODELS_TOKEN")),
  cerebras: first(read(target, "CEREBRAS_API_KEY"), read(source, "CEREBRAS_API_KEY")),
};
let existing = {};
try { existing = JSON.parse(read(target, "AI_PROVIDER_KEYS_JSON") || "{}"); } catch { throw new Error("AI_PROVIDER_KEYS_JSON is invalid."); }
const configured = Object.fromEntries(Object.entries(values).filter(([, value]) => value));
if (!Object.keys(configured).length && !Object.keys(existing).length) throw new Error("No AI provider key is configured.");
const merged = JSON.stringify({ ...existing, ...configured });
const replacement = `AI_PROVIDER_KEYS_JSON='${merged}'`;
if (/^AI_PROVIDER_KEYS_JSON=.*/m.test(target)) target = target.replace(/^AI_PROVIDER_KEYS_JSON=.*/m, replacement);
else target += `${target.endsWith("\n") ? "" : "\n"}${replacement}\n`;
fs.writeFileSync(targetPath, target, { mode: 0o600 });
NODE

chmod 600 "$TARGET"
echo "AI provider credentials synchronized without displaying secret values."
