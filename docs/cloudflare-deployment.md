# Deploy Moopiew through Cloudflare Tunnel

The project uses the same split of responsibilities as z-platform:

1. Terraform owns the proxied DNS CNAMEs for the public application hosts,
   including `chat.zeaz.dev` for NextChat.
2. An existing Cloudflare Tunnel owns the public-to-private connection.
3. `cloudflared` forwards the application to Caddy on `127.0.0.1:8080`.
4. `cloudflared` forwards the dashboard hostname to Caddy on
   `127.0.0.1:80`; Caddy applies Basic Auth and proxies to
   `127.0.0.1:8082`.
5. Cloudflare Access and Caddy Basic Auth protect `piewdash.zeaz.dev`.
6. `zok.zeaz.dev` forwards to the `/mnt/zok` Vite UI on `127.0.0.1:5175`.
   Vite proxies `/api/*` to the private Node API on `127.0.0.1:3005`; the
   API port is intentionally not exposed as a separate public origin.
7. `z-spark.zeaz.dev` forwards to Caddy on `127.0.0.1:8080`. Caddy serves the
   production build from `/mnt/z-spark/client/dist` and proxies `/api/*` to
   the private Gemini backend on `127.0.0.1:13131`.

The Arin frontend is built from `sites/arin`, published to `deploy/arin`, and
served by the host-specific Caddy route for `arin.zeaz.dev` on the same
reviewed loopback origin. Caddy proxies Arin's `/api/*`, `/preview/*`, and
`/app/*` paths to the separate loopback backend on `127.0.0.1:8787`; Arin data
is kept in the ignored `data/arin/` directory and never shares MooPiew's
database.

`cme.zeaz.dev` reaches the reviewed host-local CME/ZEAZ Python API at
`http://127.0.0.1:8000`, which is also the application's documented default.
Keep the Terraform origin and the running service on the same port; a 502 on
this hostname means the tunnel cannot reach that local origin.

NextChat (`qwen-gen-nextchat-1`) is published through the same tunnel at
`chat.zeaz.dev` and reaches the host-published port `127.0.0.1:3000`. Its
OpenAI-compatible backend is the sibling LiteLLM service at
`http://litellm:4000/v1` (`qwen-gen-litellm-1:4000` on the Compose network).
Keep the tunnel origin on the host port; do not target a container name from a
host-process cloudflared instance.

## Required operator values

Populate `.env.cloudflare` locally from the Cloudflare account that owns
`zeaz.dev`:

- `CLOUDFLARE_API_TOKEN`: scoped to the account/zone, with Zone DNS Edit,
  read/edit permission for the selected existing tunnel, and Account Access:
  Apps and Policies Edit.
- `CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_ZONE_ID`, and `CLOUDFLARE_TUNNEL_ID`.
- `CLOUDFLARE_TUNNEL_TOKEN`: only on the origin host that runs cloudflared.
- `PIEWDASH_ACCESS_ALLOWED_EMAILS`: a JSON array containing exact operator
  emails. Never use an `everyone` or domain-wide Access rule.
- `MOOPIEW_ORIGIN=http://127.0.0.1:8080` and
  `PIEWDASH_ORIGIN=http://127.0.0.1:80`. The latter must never point directly
  to port 8082 because that bypasses Caddy Basic Auth.
- `ZOK_ORIGIN=http://127.0.0.1:5175`. Keep the ZOK Node API on
  `http://127.0.0.1:3005`; the frontend's `/api` proxy handles that hop.
- `Z_SPARK_ORIGIN=http://127.0.0.1:8080`. Keep the z-spark Gemini backend on
  `http://127.0.0.1:13131`; Caddy owns the static build and `/api` proxy.

The API token and tunnel token are distinct secrets. Never commit either one.

## Provision safely

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
./scripts/start.sh
./scripts/cloudflare-plan.sh
```

If Cloudflare already has a record for any hostname, import each applicable
records before applying the reviewed plan. Confirm the plan keeps each CNAME
proxied and targets the selected tunnel. Keep `manage_tunnel_config = false`;
merge the generated ingress fragment into the existing tunnel config instead,
unless the entire existing remote configuration has been imported and
reviewed.

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
payment and Cloudflare credentials in separate ignored files. Create
`.env.dashboard` from its example, generate a random password and its Caddy
bcrypt hash, and keep the file mode `0600`. Verify all paths with
`./scripts/production-check.sh`.

Then verify `https://moopiew.zeaz.dev/api/menu`,
authenticated `https://piewdash.zeaz.dev/api/health`, `/api/ready`, and the
`https://zerp.zeaz.dev/` application route, and the customer storefront. An anonymous dashboard request must receive a Caddy
`401` or a Cloudflare Access login redirect, never dashboard data. A 502
response indicates an unreachable origin; a 530 indicates that Cloudflare
cannot reach a healthy tunnel.

## ZOK runtime and public route

Run the ZOK dashboard from `/mnt/zok` with the existing local development
process:

```bash
cd /mnt/zok
npm run dev
```

Verify both local listeners before applying the reviewed Cloudflare plan:

```bash
curl -fsS http://127.0.0.1:5175/
curl -fsS http://127.0.0.1:3005/api/db
```

After the DNS record and tunnel ingress are active, verify:

```bash
curl -fsS https://zok.zeaz.dev/
curl -fsS https://zok.zeaz.dev/api/db
```

The second public request is still served by the UI origin and forwarded by
Vite to port 3005. Do not create a second DNS route to port 3005 unless a
separate authenticated API hostname is explicitly designed and reviewed.

## z-spark runtime and public route

Build the client into the Caddy static root and keep the Gemini backend on its
private loopback port:

```bash
cd /mnt/z-spark/client
npm ci
npm run build
chmod 600 /mnt/z-spark/server/.env
pm2 status
```

The PM2-managed `omega-backend` process reads `GEMINI_API_KEYS` only from the
ignored `/mnt/z-spark/server/.env` and binds the backend to port 13131. The
browser client uses the same-origin `/api/chat` path, so the API key never
reaches the browser and no CORS exception is needed.

Verify the local route before the Cloudflare plan:

```bash
curl -fsS -H 'Host: z-spark.zeaz.dev' http://127.0.0.1:8080/
curl -fsS -o /dev/null -w '%{http_code}\n' -H 'Host: z-spark.zeaz.dev' http://127.0.0.1:8080/api/chat
```

After DNS and tunnel ingress are active, verify:

```bash
curl -fsS https://z-spark.zeaz.dev/
curl -fsS -o /dev/null -w '%{http_code}\n' https://z-spark.zeaz.dev/api/chat
```

The API check without a JSON body is expected to return `400`; a `502` means
the backend on port 13131 is unavailable.

## Arin release and runtime

On the origin host, create the ignored runtime environment from
`sites/arin/.env.arin.example`, set a unique `ARIN_CONNECTOR_KEY`, and keep the
file mode `0600`. Install the user service and build the frontend:

```bash
install -m 600 sites/arin/.env.arin.example .env.arin
# Replace ARIN_CONNECTOR_KEY with a generated Fernet key before starting.
systemctl --user daemon-reload
systemctl --user enable --now arin.service
npm --prefix sites/arin test
install -d -m 700 deploy/arin
cp -a sites/arin/dist/. deploy/arin/
sudo systemctl reload "moopiew-proxy-system@$USER.service"
```

Verify the backend before opening the public hostname:

```bash
curl -fsS http://127.0.0.1:8787/api/health
curl -fsS https://arin.zeaz.dev/api/health
```

The complete backend flow is covered by
`PYTHONPATH=sites/arin python3 sites/arin/scripts/integration-smoke.py`.
