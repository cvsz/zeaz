# zDash on Cloudflare

`zdash.zeaz.dev` is managed by the Cloudflare Terraform stack in
`zworkforce`, not in this repository. The DNS record, the tunnel ingress rule
and the Cloudflare Access application are all declared in
`infrastructure/terraform/cloudflare/zdash.tf` there. To change them, open a
pull request in that repository and let it merge before applying.

This document keeps only what belongs to this repository: the gateway it serves
and the loopback port behind it.

## Data path

```text
Browser
  -> Cloudflare Access
  -> Cloudflare Tunnel
  -> http://127.0.0.1:18080
  -> zDash local gateway
```

The origin is loopback-only. Do not publish the zDash backend, PostgreSQL, Redis, or frontend containers directly.

## Origin prerequisite

Start and verify the zDash stack first:

```bash
cd ~/zdash
git pull --ff-only origin main
sudo bash scripts/local/stack.sh up
curl -fsS http://127.0.0.1:18080/gateway-health
curl -fsS http://127.0.0.1:18080/health
```

## Cloudflare environment

Configure `.env.cloudflare` with the existing Cloudflare account, zone, tunnel, and operator allowlist. zDash inherits `PIEWDASH_ACCESS_ALLOWED_EMAILS` unless a dedicated JSON array is supplied:

```bash
ZDASH_HOSTNAME=zdash.zeaz.dev
ZDASH_ORIGIN=http://127.0.0.1:18080
ZDASH_ACCESS_ALLOWED_EMAILS='["operator@example.com"]'
```

Protect the file:

```bash
chmod 600 .env.cloudflare
```

## Existing DNS records

Cloudflare error `81053` means an A, AAAA, or CNAME record with the hostname
already exists but is not yet associated with the Terraform state. Do not delete
the record merely to make Terraform create it again.

Run these steps in `zworkforce`, which is where the state now lives. Its import
wrapper is `scripts/cloudflare-import-dns.sh` and behaves the same way:

- initializes the configured Terraform backend;
- backs up the current state before touching anything;
- queries Cloudflare DNS by exact hostname;
- skips resources already present in state;
- refuses ambiguous matches;
- never creates, updates, or deletes DNS records.

## Plan and apply

Create and display a plan, review it in full, and only then apply. Because the
tunnel also serves unrelated production hostnames, the pull request must merge
and clear review before the apply step runs.

## Tunnel configuration safety

Tunnel configuration is opt-in in the owning repository. Keep
`manage_tunnel_config` false when the ingress list is managed separately, so an
apply cannot replace unrelated ingress rules.



```bash
MANAGE_TUNNEL_CONFIG=false
```

The required ingress entry is:

```yaml
- hostname: zdash.zeaz.dev
  service: http://127.0.0.1:18080
```

It must appear before the terminal `http_status:404` rule.

## Verify

```bash
dig +short zdash.zeaz.dev CNAME
curl -I https://zdash.zeaz.dev
curl -fsS http://127.0.0.1:18080/gateway-health
```

An unauthenticated public request should be redirected to Cloudflare Access rather than reaching zDash directly.
