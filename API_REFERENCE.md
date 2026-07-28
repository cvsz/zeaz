# API Reference

[`docs/openapi.yaml`](docs/openapi.yaml) is the canonical published HTTP
contract. Runtime routing and validation are implemented in `app.py`. CI checks
that the document is valid YAML, resolves every local reference, declares
required path parameters and protected-route security, and that every published
operation is recognized by an isolated application server. It also parses the
runtime handler routes and requires exact `(method, path)` reverse parity;
new regular-expression routes require an explicitly reviewed template mapping.

Owner credentials use the ASCII-safe `X-Admin-Key-B64` header. Legacy
`X-Admin-Key` compatibility remains in the server during migration and must not
be embedded in browser source, URLs, logs, or version control.

Provider document-policy versions use end-exclusive UTC effective windows.
`PATCH /api/admin/document-requirements/{requirementId}` closes the current
version and creates one successor atomically; historical versions are
read-only and cannot authorize new uploads.
