# API Reference

[`docs/openapi.yaml`](docs/openapi.yaml) is the canonical published HTTP
contract. Runtime routing and validation are implemented in `app.py`. CI checks
selected route presence, but full bidirectional implementation-to-contract
parity is not yet automated; consumers must treat undocumented runtime routes
as internal.

Owner credentials use the ASCII-safe `X-Admin-Key-B64` header. Legacy
`X-Admin-Key` compatibility remains in the server during migration and must not
be embedded in browser source, URLs, logs, or version control.
