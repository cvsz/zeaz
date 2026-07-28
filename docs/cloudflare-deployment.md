# Deploy Moopiew through Cloudflare Tunnel

The project uses the same split of responsibilities as z-platform:

1. Terraform owns the proxied DNS CNAME for `moopiew.zeaz.dev`.
2. An existing Cloudflare Tunnel owns the public-to-private connection.
3. `cloudflared` forwards that hostname to Caddy on `127.0.0.1:8080`.
4. Caddy proxies to the MooPiew service on `127.0.0.1:8000`.

## Required operator values

Populate `.env.cloudflare` locally from the Cloudflare account that owns
`zeaz.dev`:

- `CLOUDFLARE_API_TOKEN`: scoped to the account/zone, with Zone DNS Edit and
  read/edit permission for the selected existing tunnel.
- `CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_ZONE_ID`, and `CLOUDFLARE_TUNNEL_ID`.
- `CLOUDFLARE_TUNNEL_TOKEN`: only on the origin host that runs cloudflared.

The API token and tunnel token are distinct secrets. Never commit either one.

## Provision safely

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
./scripts/start.sh
./scripts/cloudflare-plan.sh
```

If Cloudflare already has a record for `moopiew.zeaz.dev`, import that record
before applying the reviewed plan. Keep `manage_tunnel_config = false`; merge
the generated ingress fragment into the existing tunnel config instead, unless
the entire existing remote configuration has been imported and reviewed.

Start the connector on the origin host with:

```bash
./scripts/cloudflare-tunnel.sh
```

For durable user services, copy `deploy/systemd/moopiew.service`,
`deploy/systemd/moopiew-dashboard.service`, and
`deploy/systemd/moopiew-cloudflared.service` to `~/.config/systemd/user/`.
Install `deploy/systemd/moopiew-proxy-system@.service` under
`/etc/systemd/system/`; this system template runs Caddy as the selected user
with only the low-port bind capability. Then run:

```bash
systemctl --user daemon-reload
systemctl --user enable --now moopiew.service moopiew-dashboard.service moopiew-cloudflared.service
sudo systemctl daemon-reload
sudo systemctl enable --now "moopiew-proxy-system@$USER.service"
```

Create `.env.production` from its example and set unique role keys first. Keep
payment and Cloudflare credentials in separate ignored files. Verify all paths
with `./scripts/production-check.sh`.

Then verify `https://moopiew.zeaz.dev/api/menu`,
`https://piewdash.zeaz.dev/api/health`, `/api/ready`, and the customer
storefront. A 502 response indicates an unreachable origin; a 530 indicates
that Cloudflare cannot reach a healthy tunnel.
