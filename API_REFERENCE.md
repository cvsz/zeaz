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

Order completion and delivery settlement require confirmed payment. An owner
may atomically send `status=completed` with `payment_status=paid`; staff cannot
change financial state. Receipts are immutable financial snapshots issued only
after payment is confirmed, and repeated receipt or tax-invoice requests
return the existing record rather than creating another document.

Rider and merchant application reviews are serialized terminal mutations: one
pending application can produce exactly one review and audit event. Concurrent
merchant registrations for the same phone produce one pending application.
Riders assigned to non-terminal deliveries cannot be deactivated until those
deliveries are reassigned or closed.

Inventory quantities, recipe quantities, delivery rates and coordinates must
be finite numbers; `NaN` and positive or negative infinity are rejected before
SQLite mutation. Inventory adjustments serialize across processes, require a
non-empty reason and cannot produce negative stock. Settings requests must
change at least one supported key, roll back fully on invalid values and record
the exact changed keys in the audit event.
