# API Reference

[`docs/openapi.yaml`](docs/openapi.yaml) is the canonical published HTTP
contract. Runtime routing and validation are implemented in `app.py`. CI checks
that the document is valid YAML, resolves every local reference, declares
required path parameters and protected-route security, and that every published
operation is recognized by an isolated application server. Reverse parity is
not yet automated; consumers must treat undocumented runtime routes as internal.

Owner credentials use the ASCII-safe `X-Admin-Key-B64` header. Legacy
`X-Admin-Key` compatibility remains in the server during migration and must not
be embedded in browser source, URLs, logs, or version control.
