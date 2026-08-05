# zDash on Cloudflare

`zdash.zeaz.dev` is managed by the Cloudflare Terraform stack in this repository.

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

Cloudflare error `81053` means an A, AAAA, or CNAME record with the hostname already exists but is not yet associated with the Terraform state. Do not delete the record merely to make Terraform create it again.

Inspect the existing `zai`, `auth`, and `zdash` records without changing state:

```bash
./scripts/cloudflare-import-dns.sh --check
```

Import the exact existing records into state:

```bash
./scripts/cloudflare-import-dns.sh
```

The script:

- initializes the configured Terraform backend;
- backs up the current state under `backups/cloudflare/`;
- queries Cloudflare DNS by exact hostname;
- skips resources already present in state;
- refuses ambiguous matches;
- never creates, updates, or deletes DNS records.

To reconcile every DNS resource managed by the stack:

```bash
./scripts/cloudflare-import-dns.sh --all
```

## Plan and apply

Create and display a plan. The command automatically reconciles `zai`, `auth`, and `zdash` before planning:

```bash
./scripts/cloudflare-apply.sh
```

After reviewing the full plan, apply that plan explicitly:

```bash
./scripts/cloudflare-apply.sh --apply
```

To reconcile every managed DNS record first:

```bash
./scripts/cloudflare-apply.sh --all-dns
```

The apply wrapper validates formatting and configuration, backs up Terraform state, saves the plan with mode `600`, and verifies the local zDash origin after a successful apply.

## Tunnel configuration safety

The tunnel configuration remains opt-in. Import and review the live tunnel configuration before setting:

```bash
MANAGE_TUNNEL_CONFIG=true
```

When this value is true, `cloudflare-apply.sh` refuses to continue unless the existing tunnel configuration is already present in Terraform state. This prevents unrelated ingress rules from being replaced.

Keep the value false when tunnel ingress is managed separately:

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
