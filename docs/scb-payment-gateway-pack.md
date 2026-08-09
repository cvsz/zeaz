# SCB Payment Gateway Requirements Pack

Status: held and feature-gated. This document is the operator-facing form and
rollout contract for the MooPiew SCB QR integration. It contains no credentials.

## Application form

Complete this section from the approved SCB merchant application. Keep the
submitted copy in the approved secure document store, not in this repository.

| Field | Required value | Completed |
| --- | --- | --- |
| Application name | `MooPiew` | [ ] |
| Public description | `Moopiew - AI-powered restaurant ordering and food delivery platform.` | [ ] |
| Product | `qr_api` / Mae Manee QR, only if approved | [ ] |
| OAuth callback | `https://moopiew.zeaz.dev/auth/scb/callback` | [ ] |
| Payment confirmation URL | `https://moopiew.zeaz.dev/api/scb/payment/confirm` | [ ] |
| QR create contract | Mae Manee `/v1/maemanee/payment/qr/create` | [ ] |
| Transaction Inquiry contract | Mae Manee `getone` for the same product | [ ] |
| Callback signing contract | Confirmed with SCB and configured server-side | [ ] |
| Sandbox/UAT approval | Written approval or ticket reference recorded securely | [ ] |

## Billing and spending-limit form

These are server-side risk controls, not customer-editable fields. Values are
integer Thai baht and must be reviewed by an owner/risk approver before the
payment feature is enabled.

| Control | Environment key | Default template | Approved value | Owner/date |
| --- | --- | ---: | --- | --- |
| Single payment maximum | `SCB_MAX_PAYMENT_THB` | `50000` |  |  |
| Daily SCB payment budget | `SCB_DAILY_PAYMENT_LIMIT_THB` | `200000` |  |  |

The server rejects a QR creation request when the single amount exceeds the
single-payment cap or when created, pending, and paid SCB attempts for the UTC
day would exceed the daily budget. Cancelled, expired, and refunded attempts do
not consume the budget. A cap change requires a reviewed deployment and an
audit record; it must not be accepted from a public or customer form.

## Security boundary

- Keep `PAYMENTS_ENABLED=false`, `SCB_ENABLED=false`, and
  `SCB_MAEMANEE_QR_ENABLED=false` until the checklist below is complete.
- Store `.env.payment`, API secret, webhook secret, Fernet key, certificates,
  and OAuth tokens outside Git and outside browser storage.
- The callback is only a trigger. The application calls the matching SCB
  Transaction Inquiry API before setting an order to `paid`.
- Profile OAuth authorization and merchant payment authentication remain
  separate; a customer/profile token must not be reused as a payment token.

## Sandbox-to-production checklist

- [ ] Merchant/product entitlement confirmed by SCB.
- [ ] Return URL and callback URL registered exactly.
- [ ] mTLS and callback-signature requirements validated, if applicable.
- [ ] Spending caps approved and entered in the ignored `.env.payment` file.
- [ ] Preflight passes without printing secrets:
  `./scripts/scb-preflight.sh`.
- [ ] A Sandbox QR is created and its status is confirmed by Transaction Inquiry.
- [ ] Duplicate callback and repeated owner inquiry remain idempotent.
- [ ] Cancelled-order payment is recorded for reconciliation and does not reopen
  the order.
- [ ] Payment feature is enabled only through the approved rollout change.
- [ ] Rollback is `PAYMENTS_ENABLED=false`, `SCB_ENABLED=false`, restart, and
  verify that public config reports `enabled: false`.

## Source references

- [`docs/scb-application.md`](scb-application.md) — endpoint mapping and SCB
  product boundaries.
- [`.env.payment.example`](../.env.payment.example) — sanitized configuration
  contract.
- [`scripts/scb-preflight.sh`](../scripts/scb-preflight.sh) — local gate.
