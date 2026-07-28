# Live AI catalog integration

MooPiew uses an owner-only, feature-gated live AI catalog for operational
writing and analysis. It is not exposed to customers, riders or merchant
applicants. The catalog currently supports Hugging Face Inference Providers,
Gemini, NVIDIA NIM, Z.AI, OpenCode Zen and OpenRouter whenever the associated
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

## Enable locally

1. Create a Hugging Face user access token with **Inference Providers**
   permission.
2. Copy `.env.ai.example` to an ignored local file such as `.env.ai`, add only
   the provider keys approved for use, and load it into the service environment.
3. Run `./scripts/ai-preflight.sh`; use `./scripts/huggingface-preflight.sh`
   only when enabling Hugging Face chat inference. Restart the service, open
   `/ai.html`, enter the owner key and load the
   catalog.

`HF_TOKEN` stays only on the server. It is never returned by APIs, written to
the database, included in browser JavaScript, or committed to Git.

For Gemini, NVIDIA NIM, Z.AI, OpenCode Zen or OpenRouter, add a matching
`gemini`, `nvidia`, `zai`, `opencode` or `openrouter` entry to
`AI_PROVIDER_KEYS_JSON`. The catalog reads only models returned by the
provider’s live models endpoint, so an unavailable provider/model is omitted.
Z.AI is prepared at `https://api.z.ai/api/paas/v4`; it appears only after a
dedicated `zai` API key is configured.

OpenCode Zen and OpenRouter are filtered to models whose catalog metadata
declares zero input/output pricing. A provider’s free tier, rate limit and
regional availability can still change, so the page reports live provider
availability rather than promising permanent free inference.

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
