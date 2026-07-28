# Database operations

MooPiew uses SQLite at `data/moopiew.sqlite3` by default. The database uses WAL
mode, foreign keys and transactional writes. The service applies compatible
schema migrations at startup; use `./scripts/migrate.sh` to run that step
explicitly during maintenance.

## Data domains

| Domain | Examples |
| --- | --- |
| Store setup | settings, business profile, delivery pricing and zones |
| Commerce | menu, orders, order items, status history, coupons, payments |
| Delivery | rider applications, riders, assignment and tracking state |
| Partner onboarding | merchant applications and review outcome |
| Provider policy | providers, services, merchant/vehicle types and effective document requirements |
| Document workflow | uploaded documents, verification state and append-only history |
| Operations | inventory, recipes, stock movements, receipts, tax invoices |
| Customer | customer contact linkage and loyalty ledger |
| Control plane | audit log and encrypted SCB OAuth tokens when enabled |

Customer contact data, payment references, coordinates and tokens are private.
Do not place a populated database, export, `.env*`, certificate or master-data
file in Git.

The additive provider-document schema is in
`migrations/001_provider_document_requirements.sql`. Requirements are seeded
from reviewed Thailand provider references and are queried at runtime; they are
never encoded as upload buttons or environment variables.

## Backup and recovery

```bash
./scripts/health-check.sh
./scripts/backup-database.sh
```

Backups are SQLite-consistent snapshots written with `0600` permissions. To
restore, stop the service, replace only the confirmed database file from a
verified backup, restart the service, then check `/api/ready` and a test order
lookup. Keep an off-host encrypted backup according to the business retention
policy.
