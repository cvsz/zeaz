# ZEAZ One Local and Cloudflare Deployment

This repository contains the versioned ZEAZ One source bundle and a guarded
operator workflow for deploying it on the `zeaz-platform` origin host.

## Managed endpoints

| Endpoint | Origin | Delivery |
| --- | --- | --- |
| `https://one.zeaz.dev` | `http://127.0.0.1:18081` | Cloudflare Tunnel |
| `https://api.zeaz.dev/v1/products/zeaz-one` | `http://127.0.0.1:18084` | Cloudflare Tunnel |
| `https://support.zeaz.dev/zeaz-one` | `http://127.0.0.1:18083` | Cloudflare Tunnel |
| `https://www.zeaz.dev/products/zeaz-one` | n/a | Optional path-specific redirect Worker |

All application origins bind only to loopback. Cloudflare DNS records are
proxied CNAMEs to the existing tunnel. The `www` route does not change the
existing corporate Worker; it is a more specific route that redirects the ZEAZ
One product path to the primary product hostname.

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
`$HOME/services/zeaz-one/releases/`, validates it, starts the two hardened
Docker services, runs health checks, and atomically updates the `current`
symlink. The latest five releases are retained for rollback.

Review the Terraform plan. Apply only with an explicit flag:

```bash
./scripts/zeaz-one-sync.sh --skip-local --apply-cloudflare
```

To add the canonical corporate product route, first grant the scoped Cloudflare
API token `Workers Scripts Write` and `Workers Routes Write`, then run:

```bash
./scripts/zeaz-one-sync.sh --skip-local --plan-cloudflare --www-redirect
./scripts/zeaz-one-sync.sh --skip-local --apply-cloudflare --www-redirect
```

## Tunnel configuration modes

`MANAGE_TUNNEL_CONFIG=false` is the safe default. Terraform manages DNS, but an
operator must merge the ZEAZ One entries from
`deploy/cloudflared/moopiew-ingress.yml.example` into the live cloudflared
configuration before its terminal `http_status:404` rule.

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
