# ZEAZ One Runtime Bundle

Production-oriented static product sites and a read-only product API for the
ZEAZ One programme.

The services bind only to loopback:

- `127.0.0.1:18081` — `one.zeaz.dev`
- `127.0.0.1:18082` — corporate product preview
- `127.0.0.1:18083` — `support.zeaz.dev/zeaz-one`
- `127.0.0.1:18084` — `api.zeaz.dev/v1/products/zeaz-one`

Deploy through `../../scripts/zeaz-one-sync.sh`; do not expose these ports
outside the origin host.
