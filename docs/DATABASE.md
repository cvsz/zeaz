# Database operations

MooPiew uses SQLite at `data/moopiew.sqlite3` by default. The database uses WAL
mode, foreign keys and transactional writes. Ordered files under `migrations/`
are the canonical schema. The service applies them at startup through the
checksummed `schema_migrations` ledger; use `./scripts/migrate.sh` to run the
same path explicitly during maintenance. Applied migration files are immutable:
changing a name or checksum causes startup to fail closed.

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
| Control plane | audit log, encrypted SCB OAuth tokens, and expiring one-time OAuth state/PKCE verifier records |

Customer contact data, payment references, coordinates and tokens are private.
Do not place a populated database, export, `.env*`, certificate or master-data
file in Git.

The current base schema is `migrations/000_core_schema.sql`; the historical
additive provider-document migration remains
`migrations/001_provider_document_requirements.sql`, and
`migrations/002_legacy_schema.py` upgrades schemas created before the ledger.
`migrations/003_oauth_pkce.py` adds encrypted verifier storage, while
`migrations/004_inventory_invariants.sql` enforces idempotent inventory
consumption.
Requirements are seeded separately from reviewed Thailand provider references
and queried at runtime; they are never encoded as upload buttons or environment
variables.

Critical commerce mutations start with `BEGIN IMMEDIATE`, so slot-capacity,
order-state, payment, delivery, receipt and inventory decisions serialize
across independent application processes. The database also enforces one
`order_completed` inventory movement per order and ingredient. API validation
rejects non-finite inventory and recipe quantities before persistence because
SQLite can otherwise store infinity or translate `NaN` into `NULL`. Manual
stock movements require an operator reason and preserve the balance, movement
and audit record in one transaction.

Menu partial updates also use `BEGIN IMMEDIATE` because each request reads the
current row before writing a complete row. Coupon campaign timestamps are
canonical UTC values. Coupon eligibility, order creation, redemption insertion
and `used_count` increment share one immediate transaction, preserving campaign
limits under concurrent checkout.

HTTP mutation handlers build response payloads inside the transaction but write
the success response only after the database context exits and commits. This
commit-before-response boundary is required for read-after-write consistency
and prevents a late commit failure from becoming a false API success.

## Backup and recovery

```bash
./scripts/health-check.sh
./scripts/backup-database.sh
./scripts/verify-backup.sh output/backups/<backup>.sqlite3
./scripts/restore-drill.sh output/backups/<backup>.sqlite3
```

Backups are SQLite-consistent, integrity-checked snapshots with SHA-256
manifests, `0600` permissions, and 30-day local retention by default. Set
`BACKUP_AGE_RECIPIENT` to encrypt with `age`; production may enforce this with
`BACKUP_REQUIRE_ENCRYPTION=true`. Replicate encrypted outputs off-host using the
deployment's approved object-storage mechanism. To restore, stop the service,
set `BACKUP_AGE_IDENTITY` to the private age identity when verifying an
encrypted candidate, replace only the confirmed database file, restart, then
check `/api/ready` and a test order lookup. Plaintext used during backup or
verification exists only in mode-`0600` temporary files removed by traps.
`restore-drill.sh` never replaces the active database: it verifies the artifact,
copies or decrypts it into an isolated temporary directory, applies all current
migrations, and checks SQLite integrity, foreign keys, and core tables.
