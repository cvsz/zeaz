# Moopiew Cloudflare Terraform

This stack follows the Cloudflare Tunnel DNS ownership model used by
`z-platform`: a proxied CNAME sends `moopiew.zeaz.dev` to an existing tunnel,
and cloudflared forwards the request to the local preorder server.

The stack accepts the tunnel ID as either its canonical UUID or the compact
32-character identifier used by the existing z-platform environment.

## Safe setup

```bash
cp .env.cloudflare.example .env.cloudflare
chmod 600 .env.cloudflare
$EDITOR .env.cloudflare
./scripts/cloudflare-plan.sh
```

The plan script never applies. If `moopiew.zeaz.dev` already exists, import it
before planning to prevent Terraform from attempting to create a duplicate:

```bash
terraform -chdir=infrastructure/terraform/cloudflare import \
  cloudflare_dns_record.moopiew "<zone-id>/<dns-record-id>"
./scripts/cloudflare-plan.sh
```

Only after review, an operator may apply `tfplan` manually. Keep
`manage_tunnel_config = false` unless all existing ingress rules have first
been imported and reviewed. For a local cloudflared configuration, merge the
rendered `cloudflared_ingress` output before its final fallback rule.
