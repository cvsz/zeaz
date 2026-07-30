# MooPiew Architecture

The service is a dependency-light Python HTTP API backed by SQLite (WAL), with static browser clients behind proxied Cloudflare DNS, Cloudflare Tunnel, and loopback Caddy. Application ingress uses Caddy port 8080; the protected engineering dashboard uses Caddy port 80 before reaching its loopback process on port 8082. Payment, delivery, inventory, loyalty, SCB and AI integrations are server-side only. Shared TypeScript packages provide contracts and UI primitives; they do not replace API validation.

AI requests use a live provider catalog and a bounded fallback chain. Local OpenAI-compatible servers are accepted only on loopback (or HTTPS); browser clients never receive provider credentials.
