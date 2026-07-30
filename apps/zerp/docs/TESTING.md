# Testing

Run the aggregate zERP gate:

```bash
./apps/zerp/scripts/verify.sh
```

The gate runs TypeScript typechecking, a production Vite build, whitespace
validation, and a credential/placeholder scan. The protected API contract is
also checked by the repository's Python regression tests. Browser automation,
PostgreSQL module installation, upgrade, backup/restore, and localization
document rendering tests are required before any future Odoo profile can be
called production-ready.
