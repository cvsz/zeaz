# LLM Wiki and zWorkforce routes

The Cloudflare Terraform stack owns these hostnames on the existing
Cloudflare Tunnel:

| Hostname | Local origin | Status |
| --- | --- | --- |
| `llmwiki.zeaz.dev` | `http://127.0.0.1:5173` | Built LLM Wiki web client |
| `zwf.zeaz.dev` | `http://127.0.0.1:9570` | zWorkforce API (container port 9569) |

## Port contract

`/home/cvsz/llm-wiki-app` uses two local Vite listeners:

- `5173` is the authoritative public frontend origin and serves the built
  output with `vite preview`.
- `5174` is a secondary development instance. It is not routed through
  `llmwiki.zeaz.dev`; one hostname must have one deterministic primary origin.
  Give a preview instance its own hostname or path only after that is an
  explicit deployment contract.

The separate LLM Wiki desktop services are deliberately not public tunnel
origins:

- `19828` is the local LLM Wiki API.
- `19827` is the local clip server.

Both are loopback-oriented services, and neither was listening during the
route update. Sending Cloudflare Tunnel traffic directly to a loopback origin
can also make a service treat the request as a trusted local caller, bypassing
the intended LAN/token boundary. To publish either service, add an
authenticated reverse-proxy/API gateway first, then add an explicit
path/hostname route and an end-to-end auth test.

## Verification

Before applying, verify the local origins:

```bash
curl --fail http://127.0.0.1:5173/
curl --fail http://127.0.0.1:9569/health
```

After applying the Terraform plan, verify DNS, tunnel ingress, and public
responses independently. A healthy local origin alone does not prove public
Cloudflare routing.
