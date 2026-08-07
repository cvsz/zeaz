# ZEAZ One Local and Cloudflare Deployment

This repository contains the versioned ZEAZ One source bundle and a guarded
operator workflow for deploying it on the `zeaz-platform` origin host.

## Managed endpoints

| Endpoint | Local origin | Public delivery |
| --- | --- | --- |
| `https://one.zeaz.dev` | `http://127.0.0.1:18081` | Cloudflare Tunnel |
| `https://api.zeaz.dev/v1/products/zeaz-one` | `http://127.0.0.1:18084` for local parity/health | Path-specific Cloudflare Worker on the existing shared API hostname |
| `https://support.zeaz.dev/zeaz-one` | `http://127.0.0.1:18083` | Cloudflare Tunnel |
| `https://www.zeaz.dev/products/zeaz-one` | Not managed by this repository | Corporate Worker deployed from `cvsz/zeaz-platform` |

All ZEAZ One application origins bind only to loopback. Terraform creates
proxied tunnel CNAMEs only for `one.zeaz.dev` and `support.zeaz.dev`. It
deliberately does not create, import or replace the existing `api.zeaz.dev` DNS
record. Instead, a specific Workers route handles only
`/v1/products/zeaz-one*`; all other shared API routes remain untouched.

`www.zeaz.dev` is a separate corporate delivery surface. This repository must
not create a Worker route, redirect, DNS record or local preview origin for
`www.zeaz.dev/products/zeaz-one`; the canonical corporate implementation lives
in `cvsz/zeaz-platform`.

## First deployment on the origin host

```bash
cd ~
git clone https://github.com/cvsz/zeaz.git
cd zeaz
cp .env.cloudflare.example .env.cloudflare
chmod 600 .env.cloudflare
$EDITOR .env.cloudflare
./scripts/zeaz-one-sync.sh --plan-cloudflare
```

The default command copies the reviewed source bundle under
`$HOME/services/zeaz-one/releases/`, validates it, starts the hardened Docker
services, runs health checks, and atomically updates the `current` symlink. The
latest five releases are retained for rollback.

The Cloudflare token requires zone DNS and tunnel permissions for the website
and support hostnames, plus `Workers Scripts Write` and `Workers Routes Write`
for the product API path. Review the Terraform plan, then apply only with an
explicit flag:

```bash
./scripts/zeaz-one-sync.sh --skip-local --apply-cloudflare
```

## Tunnel configuration modes

`MANAGE_TUNNEL_CONFIG=false` is the safe default. Terraform manages DNS and the
ZEAZ One API Worker route, but an operator must merge only the `one.zeaz.dev`
and `support.zeaz.dev` entries from
`deploy/cloudflared/moopiew-ingress.yml.example` into the live cloudflared
configuration before its terminal `http_status:404` rule. Do not add
`api.zeaz.dev` or `www.zeaz.dev` to this tunnel fragment; they remain separate
shared/corporate delivery surfaces.

Set `MANAGE_TUNNEL_CONFIG=true` only after the existing remote tunnel
configuration has been imported into Terraform state and reviewed. The apply
wrapper refuses to manage it when the state resource is absent.

## Routine update

```bash
cd ~/zeaz
./scripts/zeaz-one-sync.sh --update
```

This performs a fast-forward-only update of `main`, stages the source bundle,
creates a new atomic local release, and leaves Cloudflare unchanged.

## Status and stop

```bash
./scripts/zeaz-one-sync.sh --status
./scripts/zeaz-one-sync.sh --stop
```

## Rollback

The current release is a symlink under `$HOME/services/zeaz-one/current`.
Select a previous directory from `$HOME/services/zeaz-one/releases`, repoint the
symlink atomically, and run:

```bash
docker compose -f <release>/docker-compose.yml up -d
```

The sync script also attempts to restore the previous deployment automatically
when a new release fails its deployment checks.
