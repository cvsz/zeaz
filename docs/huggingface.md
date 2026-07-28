# Live AI catalog integration

MooPiew uses an owner-only, feature-gated live AI catalog for operational
writing and analysis. It is not exposed to customers, riders or merchant
applicants. The catalog currently supports Hugging Face Inference Providers,
Gemini, NVIDIA NIM, Z.AI, OpenCode Zen, OpenRouter, Groq, BytePlus ModelArk, Fireworks, OpenAI, Kimi, Scaleway and Together AI whenever the associated
local key is configured. The owner page is named **ZEAZ AI Live Catalog**.

## What “all free models” means in practice

No provider can safely guarantee that every public Hugging Face model has free
hosted inference. Model availability, license, provider support and pricing are
dynamic. Instead, `/api/admin/ai/models` reads the Router catalog for the
configured token and shows every chat model currently available to it. The
owner selects a model from that live catalog; the server rejects arbitrary
model IDs outside it.

The current console is chat-only. Image, audio, embedding and self-hosted model
workloads need a separate reviewed integration.

## Optional ZeaZ Provider gateway

When the local ZeaZ Provider gateway is deployed, MooPiew can use its stable
model aliases and consolidated provider routing without putting upstream keys
in the MooPiew process. Configure the ignored `.env.ai` with a dedicated client
key and either an HTTPS endpoint or the private loopback service:

```dotenv
ZEAZ_AI_GATEWAY_URL=http://127.0.0.1:8081/v1
AI_GATEWAY_PROVIDER_TOKEN=replace-with-a-dedicated-zeaz-gateway-client-key
```

The owner-only **ZEAZ AI Live Catalog** then adds models returned by
`GET /v1/models` as `zeaz_gateway:<alias>` and calls only the gateway's fixed
`POST /v1/chat/completions` endpoint. The browser never receives the endpoint
credential. Do not reuse an upstream provider key as a gateway client key.

## Enable locally

1. Create a Hugging Face user access token with **Inference Providers**
   permission.
2. Copy `.env.ai.example` to an ignored local file such as `.env.ai`, add only
   the provider keys approved for use, and load it into the service environment.
3. When the approved credentials are in
   `/home/cvsz/zeaz-provider/.env.provider`, run
   `./scripts/sync-ai-credentials.sh` to copy only the supported AI keys into
   ignored `.env.ai` without printing them. Run `./scripts/ai-preflight.sh` to
   inspect the usable catalog, or add `--strict` to fail when any configured
   provider is unavailable. Add `--smoke` to make one short inference request
   to each provider that has a live free model; responses are not printed or
   saved. Use `./scripts/huggingface-preflight.sh` only when
   enabling Hugging Face chat inference. Restart the service, open
   `/ai.html`, enter the owner key and load the
   catalog.

`./scripts/check-ai-provider-keys.sh` probes the official model-list endpoint
for every supported key found in the provider vault and writes a
credential-free health report to `output/ai-provider-health.json`. It does not
copy a key, print a key, or store provider response bodies.

BytePlus ModelArk keys are scoped to their region and project. The checker uses
the official Southeast Asia data-plane endpoint and deliberately leaves a
failing BytePlus key out of the runtime catalog until that endpoint authorizes
it; this prevents a mismatched regional key from being presented as usable.
Use `ARK_API_KEY` for a ModelArk inference key. `BYTEPLUS_API_KEY` remains a
temporary vault alias only, so existing installations can migrate safely.

For an operator refresh, run `./scripts/refresh-ai-catalog.sh`. It performs the
credential sync, writes the credential-free health report, restarts the local
service and runs the free-provider smoke checks in that order.

During sync, provider-specific keys already present in ignored `.env.ai` take
precedence over vault aliases. This includes `MOONSHOT_API_KEY` for Kimi and
`SCW_SECRET_KEY` for Scaleway, so a provider's locally issued credential is not
silently replaced by a generic vault value.

`HF_TOKEN` stays only on the server. It is never returned by APIs, written to
the database, included in browser JavaScript, or committed to Git.

For Gemini, NVIDIA NIM, Z.AI, OpenCode Zen or OpenRouter, add a matching
`gemini`, `nvidia`, `zai`, `opencode`, `openrouter`, `groq`, `byteplus`, `fireworks`, `openai`, `kimi`, `scaleway` or `together` entry to
`AI_PROVIDER_KEYS_JSON`. The catalog reads only models returned by the
provider’s live models endpoint, so an unavailable provider/model is omitted.
Z.AI is prepared at `https://api.z.ai/api/paas/v4`; it appears only after a
dedicated `zai` API key is configured.

Set `AI_DISABLED_PROVIDERS` to a comma-separated set of provider names when an
account is suspended, under billing review, or operationally disallowed. The
credential remains in the ignored server environment for controlled recovery,
but the provider is excluded from model discovery and chat routing. Remove a
name only after `./scripts/ai-preflight.sh --strict` succeeds.

OpenRouter is filtered to models whose catalog metadata declares zero
input/output pricing. OpenCode is treated the same only if its catalog supplies
zero-price metadata; OpenCode Zen itself can require billing and credits.
Groq models are listed from the configured project and are labelled free-tier
because Groq publishes Free Plan model rate limits; the account billing tier is
not exposed by its models API. Gemini and NVIDIA NIM expose live model catalogs
but do not expose universal
per-model free-price metadata through the endpoint, so they are shown as
available models—not incorrectly labelled as free. A provider’s free tier,
rate limit and regional availability can still change, so the page reports
live provider availability rather than promising permanent free inference.

## Privacy and control

- Do not paste customer names, phone numbers, addresses, payment references,
  keys or other personal data into prompts.
- AI prompts and outputs are deliberately not stored. The audit record contains
  only the selected model and response length.
- Requests are limited to 12,000 input characters and 2,048 output tokens.
- The router base URL is fixed to `https://router.huggingface.co/v1`; an
  environment value cannot turn the feature into a generic proxy.
- `HF_ENABLED=false` is the production default. Disable it immediately when a
  token is rotated or a model/provider is not approved.

Official reference: [Hugging Face Inference Providers](https://huggingface.co/docs/inference-providers/en/index).
