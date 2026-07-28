# Moopiew Cloudflare Terraform

This stack follows the Cloudflare Tunnel DNS ownership model used by
`z-platform`: proxied CNAMEs send `moopiew.zeaz.dev` and
`piewdash.zeaz.dev` to an existing tunnel. Cloudflared forwards the app to
Caddy on 8080; the shared wildcard ingress reaches Caddy on port 80, where a
host-specific route proxies the dashboard to loopback port 8082.
Terraform also owns the dashboard's Cloudflare Access application. Its allow
policy accepts only the exact, nonempty email set supplied through
`PIEWDASH_ACCESS_ALLOWED_EMAILS`; domain-wide and `everyone` rules are
deliberately unsupported. Caddy Basic Auth protects the origin as a second
layer.

The stack accepts the tunnel ID as either its canonical UUID or the compact
32-character identifier used by the existing z-platform environment.

## Safe setup

```bash
cp .env.cloudflare.example .env.cloudflare
chmod 600 .env.cloudflare
$EDITOR .env.cloudflare
./scripts/cloudflare-plan.sh
```

The API token needs Zone DNS Edit, Tunnel Read/Edit, and Account Access: Apps
and Policies Edit. `PIEWDASH_ACCESS_ALLOWED_EMAILS` must be a JSON array of
individual operator email addresses.

## Remote state

`backend.r2.tf.example` is the canonical encrypted S3-compatible R2 backend
with an S3 lockfile. The state script installs it as ignored `backend.tf` only
in R2 mode and removes a newly installed copy if initialization fails. Bucket,
endpoint and S3 credentials are partial configuration supplied only from the
mode-`0600` ignored `.env.cloudflare`; credentials are never written to
Terraform source or command-line backend arguments.

Keep `TERRAFORM_BACKEND_TYPE=local` and `ALLOW_R2_WRITE=false` until a private,
dedicated R2 bucket and a bucket-scoped Object Read & Write access pair exist.
Then take an independent copy of the current local state and migrate:

```bash
TERRAFORM_BACKEND_TYPE=r2
ALLOW_R2_WRITE=true
TERRAFORM_STATE_BUCKET=replace-with-private-state-bucket
CLOUDFLARE_S3_API_ENDPOINT=https://<account-id>.r2.cloudflarestorage.com
CLOUDFLARE_ACCESS_KEY_ID=replace-with-bucket-scoped-access-key
CLOUDFLARE_ACCESS_SECRET_KEY=replace-with-bucket-scoped-secret
./scripts/cloudflare-state.sh migrate
./scripts/cloudflare-state.sh verify
./scripts/cloudflare-plan.sh
```

Migration refuses an empty local state, stores a mode-`0600` backup plus
SHA-256 under ignored `output/backups/`, and requires the exact managed
resource-address set before and after migration. Preserve that backup outside
the origin host. To recover, first stop all Terraform writers, verify the
backup checksum, switch explicitly to a reviewed empty recovery backend, and
use `terraform state push` only after a no-change import/plan review. Never
disable `use_lockfile` to bypass a lock; investigate the current writer first.

The plan script never applies. If either hostname already exists, import it
before planning to prevent Terraform from attempting to create a duplicate:

```bash
terraform -chdir=infrastructure/terraform/cloudflare import \
  cloudflare_dns_record.moopiew "<zone-id>/<dns-record-id>"
terraform -chdir=infrastructure/terraform/cloudflare import \
  cloudflare_dns_record.piewdash "<zone-id>/<dns-record-id>"
./scripts/cloudflare-plan.sh
```

Only after review, an operator may apply `tfplan` manually. Keep
`manage_tunnel_config = false` unless all existing ingress rules have first
been imported and reviewed. For a local cloudflared configuration, merge the
rendered `cloudflared_ingress` output before its final fallback rule.
