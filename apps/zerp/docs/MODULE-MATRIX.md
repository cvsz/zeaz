# Module matrix

| Capability | Current classification | Evidence / boundary |
| --- | --- | --- |
| Receipts and tax invoices | `external-integration` | Read-only data from `/api/admin/operations` |
| Receipt journal projection | `zerp-custom` | Balanced immutable receipt projection at `/api/admin/zerp/accounting/entries` |
| Inventory and reorder visibility | `external-integration` | Existing inventory API data |
| Inventory movement journal | `zerp-custom` | Owner-only projection at `/api/admin/zerp/inventory/moves`; source/destination are operational labels |
| Menu recipes | `external-integration` | Existing `menu_recipes` data |
| CRM application overview | `external-integration` | Existing merchant/rider applications |
| Workforce overview | `external-integration` | Existing riders API data |
| Double-entry general ledger | `deferred-with-rationale` | No ledger model or posting workflow exists |
| Payroll and attendance | `deferred-with-rationale` | No HR/payroll model or localization review exists |
| Multi-level MRP and costing | `deferred-with-rationale` | Existing recipes are not a BOM/work-order engine |
| Licensed Odoo Enterprise modules | `upstream-enterprise-licensed` | Deferred pending entitlement and source decision |
