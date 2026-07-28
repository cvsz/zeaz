# MooPiew roadmap

This roadmap describes the restaurant platform, not a promise that every
payment or marketplace feature is already enabled. Dates are prioritisation
guidance and must be reviewed against merchant, legal and operational approval.

## Delivered foundation

- Customer ordering for pickup and distance-priced delivery.
- Configurable menus, inventory recipes, coupons, loyalty, receipts and audit
  history.
- Owner operations, rider/merchant applications, rider management and delivery
  tracking.
- SQLite backups, Cloudflare Tunnel deployment, health checks and API docs.
- SCB integration boundaries, Sandbox preflight and inquiry-first payment
  safety; live SCB payment remains disabled by default.

## Next: operational hardening

1. Complete store master data review, delivery-service levels and rider
   verification checklist.
2. Add role-specific authenticated rider workflows rather than sharing owner
   operations access.
3. Add export/reconciliation reports, retention controls and incident runbooks.
4. Exercise backup restore, cancellation/refund and failed-delivery scenarios.

## Next: trusted payments and partners

1. Complete SCB Sandbox QR end-to-end using approved merchant credentials,
   transaction inquiry and callback signature rules.
2. Obtain production approval, rotate secrets and launch behind feature gates.
3. Give approved merchants a scoped portal and multi-store configuration;
   preserve owner approval and audit trails.

## Later: scale

- Multi-store catalogue, service areas, commissions and settlement reporting.
- Native rider/customer apps backed by the same API contract.
- Move to managed relational storage and workers only when load and recovery
  requirements justify it.

## Definition of done

A roadmap item is complete only when its owner, security boundary, test path,
operational metric and rollback path are documented and verified in a
non-production environment.
