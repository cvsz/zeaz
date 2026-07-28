# Owner operations

Open `/ops.html` with the `X-Admin-Key` configured for the service. The key is
an owner secret: do not place it in a public client, URL, screenshot or Git.

## First-time setup

1. Complete the business profile before issuing tax invoices.
2. Configure the store coordinates, base fee, per-kilometre fee, maximum range
   and delivery zones. The server calculates fees; do not rely on a browser
   calculation.
3. Set menu items and their display order, then create inventory items and
   recipes where stock needs automatic deduction.
4. Review rider and merchant applications. Approve only after verifying the
   submitted contact and operational details; activate riders separately.
5. Create coupons only with a documented campaign owner, limits and expiry.

Keep populated `templates/store-master-data.json` local. It may contain store
coordinates, contacts or tax information and must not be committed.

## Daily flow

1. Monitor new orders and verify their payment state according to the selected
   payment method.
2. For delivery, assign an active available rider and progress the status:
   `queued` → `assigned` → `picked_up` → `on_the_way` → `delivered`.
3. For pickup, prepare and hand over only after checking the order reference.
4. Complete the order once. This performs the applicable loyalty and inventory
   movements; avoid manually repeating those actions.
5. Issue a receipt or VAT invoice only from the confirmed order/receipt record.

Cancellation is an exception path. Confirm the reason before cancelling because
the platform restores eligible coupon/loyalty state only once.

## Delivery pricing and tracking

Distance pricing is configurable: `ceil(base fee + per-km fee × calculated
distance)`, subject to the configured range. A missing store coordinate or an
out-of-range customer location must block delivery checkout rather than silently
charging a guessed fee. Customer tracking uses a tracking code and server-sent
updates; it exposes status, not private delivery details.

## Payment controls

Cash and transfer reconciliation remain an owner process. SCB QR/EASY features
must stay disabled until SCB approval, Sandbox verification, mTLS material when
required, and provider transaction inquiry are working. A QR scan, redirect or
callback alone is never proof of payment.

## End-of-day

- Review completed, cancelled and failed orders; reconcile cash/digital totals.
- Review rider assignments, unavailable riders and delivery failures.
- Count high-value inventory and record an auditable adjustment when needed.
- Run `./scripts/backup-database.sh` and confirm the backup is stored securely.
- Review the audit log for unexpected owner changes.

At least monthly and before a migration release, run
`./scripts/restore-drill.sh <backup>` against the newest replicated backup.
Record the artifact checksum, drill time, result, operator and recovery-time
measurement in the operational evidence system. The drill uses an isolated
copy and must never target the active database.
