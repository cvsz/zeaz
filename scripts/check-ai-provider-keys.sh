#!/usr/bin/env bash
# Probe known official model-list endpoints without printing or storing secrets.
# A JSON health report (no credentials or response bodies) is written to output/.
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE="${1:-/home/cvsz/zeaz-provider/.env.provider}"
REPORT="$ROOT/output/ai-provider-health.json"

[[ -f "$SOURCE" ]] || { echo "Credential source not found." >&2; exit 1; }
command -v node >/dev/null 2>&1 || { echo "Node.js is required." >&2; exit 1; }
mkdir -p "$(dirname "$REPORT")"

SOURCE="$SOURCE" REPORT="$REPORT" node <<'NODE'
const fs = require("fs");
const https = require("https");
const source = fs.readFileSync(process.env.SOURCE, "utf8");
const read = (key) => {
  const line = source.split(/\r?\n/).find((row) => row.startsWith(`${key}=`));
  return line ? line.slice(key.length + 1).trim().replace(/^['"]|['"]$/g, "") : "";
};
const probes = [
  ["anthropic", "ANTHROPIC_API_KEY", "https://api.anthropic.com/v1/models", (key) => ({"x-api-key": key, "anthropic-version": "2023-06-01"})],
  ["byteplus", ["ARK_API_KEY", "BYTEPLUS_API_KEY"], "https://ark.ap-southeast.bytepluses.com/api/v3/models", (key) => ({authorization: `Bearer ${key}`})],
  ["cerebras", "CEREBRAS_API_KEY", "https://api.cerebras.ai/v1/models", (key) => ({authorization: `Bearer ${key}`})],
  ["deepseek", "DEEPSEEK_API_KEY", "https://api.deepseek.com/models", (key) => ({authorization: `Bearer ${key}`})],
  ["fireworks", "FIREWORKS_API_KEY", "https://api.fireworks.ai/inference/v1/models", (key) => ({authorization: `Bearer ${key}`})],
  ["gemini", "GEMINI_API_KEY", "https://generativelanguage.googleapis.com/v1beta/models", (key) => ({"x-goog-api-key": key})],
  ["groq", "GROQ_API_KEY", "https://api.groq.com/openai/v1/models", (key) => ({authorization: `Bearer ${key}`})],
  ["huggingface", "HF_TOKEN_API_KEY", "https://router.huggingface.co/v1/models", (key) => ({authorization: `Bearer ${key}`})],
  ["kimi", "KIMI_API_KEY", "https://api.moonshot.ai/v1/models", (key) => ({authorization: `Bearer ${key}`})],
  ["mistral", "MISTRAL_API_KEY", "https://api.mistral.ai/v1/models", (key) => ({authorization: `Bearer ${key}`})],
  ["nvidia", "NVIDIA_NIM_API_KEY", "https://integrate.api.nvidia.com/v1/models", (key) => ({authorization: `Bearer ${key}`})],
  ["novita", "NOVITA_API_KEY", "https://api.novita.ai/v3/openai/models", (key) => ({authorization: `Bearer ${key}`})],
  ["openai", "OPENAI_API_KEY", "https://api.openai.com/v1/models", (key) => ({authorization: `Bearer ${key}`})],
  ["opencode", "OPENCODE_API_KEY", "https://opencode.ai/zen/v1/models", (key) => ({authorization: `Bearer ${key}`})],
  ["openrouter", "OPENROUTER_API_KEY", "https://openrouter.ai/api/v1/models", (key) => ({authorization: `Bearer ${key}`})],
  ["sambanova", "SAMBANOVA_API_KEY", "https://api.sambanova.ai/v1/models", (key) => ({authorization: `Bearer ${key}`})],
  ["scaleway", "SCALEWAY_API_KEY", "https://api.scaleway.ai/v1/models", (key) => ({authorization: `Bearer ${key}`})],
  ["together", "TOGETHER_API_KEY", "https://api.together.xyz/v1/models", (key) => ({authorization: `Bearer ${key}`})],
  ["zai", "ZAI_API_KEY", "https://api.z.ai/api/paas/v4/models", (key) => ({authorization: `Bearer ${key}`})],
];
const request = (url, headers) => new Promise((resolve) => {
  const req = https.request(url, {method: "GET", headers: {accept: "application/json", "user-agent": "MooPiew-ZEAZ/1.0", ...headers}, timeout: 15000}, (res) => {
    let size = 0, body = "";
    res.on("data", (chunk) => { if (size < 1_000_000) { body += chunk; size += chunk.length; } });
    res.on("end", () => {
      let count = null;
      try { const json = JSON.parse(body); const rows = Array.isArray(json.data) ? json.data : Array.isArray(json.models) ? json.models : null; count = rows ? rows.length : null; } catch {}
      resolve({status: res.statusCode || 0, models: count});
    });
  });
  req.on("timeout", () => req.destroy(new Error("timeout")));
  req.on("error", () => resolve({status: 0, models: null}));
  req.end();
});
(async () => {
  const results = [];
  for (const [provider, variable, url, makeHeaders] of probes) {
    const variables = Array.isArray(variable) ? variable : [variable];
    const selected = variables.find((name) => read(name));
    const key = selected ? read(selected) : "";
    if (!key) { results.push({provider, variable: variables.join("|"), configured: false, live: false, status: null, models: null}); continue; }
    const response = await request(url, makeHeaders(key));
    results.push({provider, variable: selected, configured: true, live: response.status >= 200 && response.status < 300, status: response.status || null, models: response.models});
  }
  const report = {generatedAt: new Date().toISOString(), results};
  fs.writeFileSync(process.env.REPORT, JSON.stringify(report, null, 2) + "\n", {mode: 0o600});
  for (const row of results) console.log(`${row.provider}: ${row.live ? "live" : "unavailable"}${row.status ? ` (HTTP ${row.status})` : ""}${Number.isInteger(row.models) ? `, ${row.models} models` : ""}`);
  console.log(`Wrote credential-free report: ${process.env.REPORT}`);
})();
NODE
