# Database operations

Moopiew uses SQLite at `data/moopiew.sqlite3` today. The database enables WAL
and foreign keys and includes settings, menu items, orders, order items, order
history and audit logs. On first boot, the application imports legacy JSON data
without deleting it.

## Lifecycle

```bash
./scripts/health-check.sh
./scripts/backup-database.sh
```

Backups are SQLite-consistent snapshots, written with `0600` permissions. Stop
the app before replacing a database during recovery; then start the service and
verify `/api/ready`.
