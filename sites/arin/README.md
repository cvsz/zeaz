# Arin app builder

This directory contains the Arin marketing/docs frontend and the loopback app
builder backend. The frontend is built with Vite; the Python service stores
accounts, workspaces, projects, versions, assets, and publish state in the
private `data/arin` directory.

## Local validation

```bash
npm ci
npm test
PYTHONPATH=sites/arin python3 -m unittest discover -s sites/arin/tests -p 'test_*.py' -v
PYTHONPATH=sites/arin python3 sites/arin/scripts/integration-smoke.py
```

The production artifact is generated at `dist/` and published to the ignored
`deploy/arin/` directory on the origin host. Caddy serves that artifact for
the marketing/docs routes and proxies `/api/*`, `/preview/*`, and `/app/*` to
the backend on `127.0.0.1:8787`.

To run the backend manually, copy `.env.arin.example` to the ignored root
`.env.arin`, generate an installation Fernet key for `ARIN_CONNECTOR_KEY`, and
start:

```bash
PYTHONPATH=sites/arin python3 -m arin_app.server
```
