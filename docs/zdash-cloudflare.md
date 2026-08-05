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

## Terraform plan

Configure `.env.cloudflare` with the existing Cloudflare account, zone, tunnel, and operator allowlist. zDash inherits `PIEWDASH_ACCESS_ALLOWED_EMAILS` unless a dedicated JSON array is supplied:

```bash
ZDASH_HOSTNAME=zdash.zeaz.dev
ZDASH_ORIGIN=http://127.0.0.1:18080
ZDASH_ACCESS_ALLOWED_EMAILS='["operator@example.com"]'
```

Then run:

```bash
chmod 600 .env.cloudflare
./scripts/cloudflare-plan.sh
```

The tunnel configuration remains opt-in. Import and review the live tunnel configuration before setting:

```bash
MANAGE_TUNNEL_CONFIG=true
```

Applying a tunnel configuration without importing the existing remote resource may replace unrelated ingress rules.

## Apply and verify

After reviewing the plan:

```bash
set -a
source .env.cloudflare
set +a

export TF_VAR_cloudflare_api_token="$CLOUDFLARE_API_TOKEN"
export TF_VAR_cloudflare_account_id="$CLOUDFLARE_ACCOUNT_ID"
export TF_VAR_cloudflare_zone_id="$CLOUDFLARE_ZONE_ID"
export TF_VAR_cloudflare_tunnel_id="$CLOUDFLARE_TUNNEL_ID"
export TF_VAR_piewdash_access_allowed_emails="$PIEWDASH_ACCESS_ALLOWED_EMAILS"
export TF_VAR_manage_tunnel_config="${MANAGE_TUNNEL_CONFIG:-false}"

terraform -chdir=infrastructure/terraform/cloudflare apply
```

Verify DNS and the Access boundary:

```bash
dig +short zdash.zeaz.dev CNAME
curl -I https://zdash.zeaz.dev
```

An unauthenticated request should be redirected to Cloudflare Access rather than reaching zDash directly.
