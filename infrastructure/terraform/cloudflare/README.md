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
