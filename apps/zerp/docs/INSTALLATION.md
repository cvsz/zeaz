# Installation

## Development

```bash
cd /home/cvsz/zeaz
npm install
npm run build --workspace @moopiew/zerp
npm run preview --workspace @moopiew/zerp
```

The preview listens on `127.0.0.1:3001`. The API must be available at the
same origin or `VITE_API_URL` must point to the MooPiew service.

## Production

Build the app and run the reviewed unit in `deploy/systemd/zerp.service`.
Expose it only through Caddy and the Cloudflare Tunnel. Do not publish port
3001 directly. Production deployment still requires explicit DNS, TLS,
backup, secret, and rollback approval.
