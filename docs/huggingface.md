# Hugging Face AI integration

MooPiew integrates Hugging Face **Inference Providers** through the official
Router. It is an owner-only, feature-gated assistant for operational writing
and analysis; it is not exposed to customers, riders or merchant applicants.

## What “all free models” means in practice

No provider can safely guarantee that every public Hugging Face model has free
hosted inference. Model availability, license, provider support and pricing are
dynamic. Instead, `/api/admin/ai/models` reads the Router catalog for the
configured token and shows every chat model currently available to it. The
owner selects a model from that live catalog; the server rejects arbitrary
model IDs outside it.

The router’s OpenAI-compatible chat endpoint is chat-only. Image, audio,
embedding and self-hosted model workloads need a separate reviewed integration.

## Enable locally

1. Create a Hugging Face user access token with **Inference Providers**
   permission.
2. Copy `.env.ai.example` to an ignored local file such as `.env.ai`, set
   `HF_ENABLED=true`, and load it into the service environment.
3. Run `./scripts/huggingface-preflight.sh`, restart the service, open
   `/ai.html`, enter the owner key and load the
   catalog.

`HF_TOKEN` stays only on the server. It is never returned by APIs, written to
the database, included in browser JavaScript, or committed to Git.

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
