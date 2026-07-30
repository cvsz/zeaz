# zERP architecture

The current production path is:

```text
Browser -> Cloudflare Tunnel -> Caddy -> zERP preview :3001
                                      -> MooPiew API :8000
                                      -> SQLite operational database
```

The browser never becomes a source of truth. It sends the owner credential in
the `X-Admin-Key-B64` request header and reads the protected operations
contract. The key is held in React state only. The zERP preview is stateless;
all mutations remain in the reviewed MooPiew owner APIs.

An Odoo/PostgreSQL profile is documented as a future option only. It must not
be enabled until the licensing, tenancy, migration, and backup decisions in the
SSOT are approved.

Issued receipts are projected idempotently into `ledger_entries` and
`ledger_lines` by migration 005. Each posted entry has matching debit and
credit totals. This read-only projection does not replace accountant-reviewed
adjustments or a complete general ledger.
