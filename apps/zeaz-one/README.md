# ZEAZ One Runtime Bundle

Production-oriented ZEAZ One product and support sites plus a read-only product
API for the ZEAZ One programme.

The services bind only to loopback:

- `127.0.0.1:18081` — `one.zeaz.dev`
- `127.0.0.1:18083` — `support.zeaz.dev/zeaz-one`
- `127.0.0.1:18084` — local API parity/health for `api.zeaz.dev/v1/products/zeaz-one`

The corporate website and `https://www.zeaz.dev/products/zeaz-one` are owned and
deployed by `cvsz/zeaz-platform`. This bundle intentionally does not publish or
redirect any `www.zeaz.dev` route.

Deploy through `../../scripts/zeaz-one-sync.sh`; do not expose these ports
outside the origin host.
