# SCB application registration — MooPiew

> **Status: held / feature-gated.** Do not enable SCB checkout in production
> until the merchant has SCB approval and a successful Sandbox payment has been
> verified by the corresponding Transaction Inquiry API.

Use these values in the SCB developer/merchant application form.

| Field | Value |
| --- | --- |
| App name | `MooPiew` |
| Public description | `Moopiew - AI-powered restaurant ordering and food delivery platform.` |
| Callback URL | `https://moopiew.zeaz.dev/auth/scb/callback` |
| Merchant name (Credit Card) | `MOOPIEW` |
| Merchant name (Direct Debit) | `MOOPIEW` |
| Biller name | `MOOPIEW` |
| Required CVV | Enabled |
| Payment confirmation endpoint | `https://moopiew.zeaz.dev/api/scb/payment/confirm` |
| Direct Debit registration callback | `https://moopiew.zeaz.dev/api/scb/direct-debit/register/callback` |
| Direct Debit payment callback | `https://moopiew.zeaz.dev/api/scb/direct-debit/payment/callback` |

Select only SCB products approved for this merchant. Do not enable production
payments until SCB has provided the merchant credentials, UAT API specification,
and callback signing/verification requirements. An unsigned callback may be a
trigger only; the application never sets an order to `paid` without an SCB
Transaction Inquiry result.

## Sandbox QR profile

Keep sandbox merchant, biller, terminal and reference identifiers only in the
ignored `.env.payment` file. Generate a unique invoice and references for every
payment attempt; never reuse the portal's sample invoice or references in
production.

## QR order mapping

For each Moopiew order, generate a new SCB QR request with:

| SCB field | Moopiew source |
| --- | --- |
| `partnerReferenceNo` | Unique payment-attempt reference, not a reused sample invoice |
| `walletId` | `SCB_BILLER_ID` issued by SCB |
| `paymentType` | `T30` for PromptPay/Thai QR initially |
| `amount` | Server-calculated order total with two decimal places |
| `partnerOrderDate` | Server timestamp in ISO 8601 format including UTC offset |
| `partnerMetaData.product` | Sanitised order line items, maximum 20 records |

Persist the SCB `orderId`, QR references and expiry alongside the order. Mark
payment as `paid` only after a verified SCB confirmation or inquiry response;
the QR image is base64 response data and should be rendered only for its
associated order.

Use `SCB_QR_INQUIRY_ENDPOINT` (`/v1/maemanee/payment/transaction/getone`) to
check a single QR payment if the confirmation webhook has not arrived. Keep the
query rate low and treat a successful inquiry response as an idempotent update
of the same payment attempt.

`SCB_QR_RECONCILIATION_ENDPOINT` (`/v1/maemanee/payment/transaction/getlist`)
is for scheduled reconciliation by wallet and payment-date range. Limit each
call to the approved date window and page size, then match results to stored SCB
order IDs/references; do not use it as high-frequency customer-facing polling.
Use the standard `Content-Type: application/json` header.

## API selection

`/v1/maemanee/payment/qr/create` is the selected integration for Moopiew because
its merchant flow returns an SCB order identifier and is paired with the Mae
Manee payment confirmation and `getone` inquiry endpoints. SCB's separate
`/v2/payment/qrcode/create` endpoint is stored as the disabled `SCB_QR30_*`
alternative. Do not combine the create endpoint from one product with the
inquiry or callback contract of the other; enable only the API product approved
for the merchant profile.

### Product catalog and enablement gates

All endpoints are present in `.env.payment.example`, but every product other
than the existing Mae Manee QR path is disabled by default. Set both its
`SCB_*_ENABLED=true` gate and include the product in `SCB_ENABLED_PRODUCTS`
only after SCB has approved the merchant, request schema, response identifiers,
and callback contract.

| Product | Operations configured | Required persisted identifier / safe completion rule |
| --- | --- | --- |
| SCB EASY App Payment | Deeplink create and transaction lookup | `transactionId`; use `/v2/transactions/{transactionId}` before paid |
| Standard QR / QR CS | QR v1/v2 create, credit-card QR lookup and void | `qrId`; lookup before paid; void never refunds by itself |
| Bill Payment | Transaction lookup plus v1/v3 inquiry | `transRef` and documented query/input fields; inquiry before paid |
| Alipay+ / WeChatPay | QR create, inquire, cancel, QR cancel, refund and pay | provider transaction/QR identifier; inquiry before paid or refunded |
| B Scan C | RTP confirm and refund | SCB payment reference; only success response settles/refunds |
| Direct Debit | registration init/inquiry, direct/web pay and payment inquiry | registration and payment IDs; callback triggers server inquiry |
| API Credit/Debit Transfer | credit/debit initiate, confirm and inquiry | transfer reference; initiation alone is never settlement |

Direct Debit callbacks remain `/api/scb/direct-debit/register/callback` and
`/api/scb/direct-debit/payment/callback` in the SCB registration form. They
must be authenticated according to SCB's product-specific signing contract and
must run the related inquiry before any internal state transition.

The downloaded Direct Debit encryption key is configured through
`SCB_DIRECT_DEBIT_ENCRYPTION_PUBLIC_KEY_FILE`. MooPiew accepts the bank-issued
Base64 public-key file locally, validates its presence before Direct Debit can
be enabled, and ignores it in Git. Never store a private key in this repository.

SCB's corporate Sandbox certificate and `privateKey.pem` are separate mTLS
credentials. Install them as `secrets/scb/certificate.crt` and
`secrets/scb/privateKey.pem`, then set `SCB_MTLS_REQUIRED=true`. The preflight
script and SCB HTTP client refuse a required mTLS configuration when either file
is absent or invalid. Rotate an Application Key or private key that has been
shared outside the approved secret store.

## Application implementation

When `PAYMENTS_ENABLED=true` and `SCB_ENABLED=true`, the ordering API exposes
SCB QR as an opt-in payment method. It creates one persistent payment attempt
per order, stores SCB's order/reference values and the base64 QR image, and
returns that image only to the customer who proves the order phone number.

The payment-confirmation route is `/api/scb/payment/confirm`. It treats the
callback only as a trigger and verifies every payment by calling SCB's `getone`
inquiry with the stored order/reference before changing state. If SCB provides
a callback signing contract, configure `SCB_WEBHOOK_SECRET` and
`SCB_WEBHOOK_SIGNATURE_HEADER` to add HMAC-SHA256 verification; an invalid
configured signature is rejected. An owner can use the protected fallback
inquiry route when a callback is missing.

### Verification rule for every SCB payment channel

Use the inquiry API belonging to the product that created the payment.  Store
the provider identifier on the payment attempt; never attempt to infer it from
the QR image or a client-supplied value.

| Channel | Stored identifier | Inquiry endpoint configuration | Transport |
| --- | --- | --- | --- |
| QR 30 / Mae Manee Tag 30 | Mae Manee `orderId`, partner reference and wallet ID | `SCB_QR_INQUIRY_ENDPOINT` | Mae Manee `getone` request |
| SCB Bill Payment | SCB transaction reference (`transRef`) plus the documented query parameter | `SCB_BILLPAYMENT_INQUIRY_ENDPOINT` | `GET /v1/payment/billpayment/transactions/{transRef}` |
| QR CS | SCB `qrId` | `SCB_QRCS_INQUIRY_ENDPOINT` | `GET /v1/payment/qrcode/creditcard/{qrId}` |
| Alipay+ / WeChatPay | Provider transaction/QR identifier returned at creation | `SCB_EWALLET_INQUIRY_ENDPOINT` | e-wallet inquiry request |
| SCB EASY App payment | Deeplink `transactionId` | `SCB_EASY_TRANSACTION_INQUIRY_ENDPOINT` | `GET /v2/transactions/{transactionId}` |

The QR 30 adapter currently enabled in Moopiew uses the first row. The other
endpoint variables are deliberately configured but not offered at checkout
until their create-response identifiers and SCB-approved request contracts are
implemented. This prevents an e-wallet or card transaction being checked with
the Mae Manee QR API.

Never mark an order paid from a customer redirect, QR scan, or callback payload
alone. Use SCB Transaction Inquiry as the source of truth for every channel:

| Channel | Verification |
| --- | --- |
| QR 30 (Thai QR/PromptPay) | Mae Manee Transaction Inquiry (`getone`) |
| QR CS | Transaction Inquiry using the SCB QR transaction identifier |
| Alipay+ / WeChatPay | Transaction Inquiry using the provider transaction identifier |
| SCB EASY App Payment | Transaction Inquiry using the Deeplink `transactionId` |

Callbacks and redirects are retained as low-latency triggers for these
inquiries; they are not payment proof. This rule applies to both Sandbox and
production.

SCB EASY authorization is started by an owner through
`GET /api/admin/scb/auth/start` and returns a one-time SCB callback URL. The
registered `/auth/scb/callback` exchanges the authorization code server-side.
Access and refresh tokens are encrypted in SQLite using the local
`SCB_TOKEN_ENCRYPTION_KEY`; they must never be placed in a committed file or
browser storage.

## Enablement checklist

Run `./scripts/scb-preflight.sh` before setting both `PAYMENTS_ENABLED=true`
and `SCB_ENABLED=true`. It checks the local configuration, encrypted OAuth
connection when the selected payment grant needs it, without printing
credentials. With `SCB_PAYMENT_OAUTH_MODE=client_credentials`, profile consent
is not a preflight requirement. Keep the feature disabled until this command
succeeds and a Sandbox QR payment has been confirmed by its SCB Transaction
Inquiry response.

## OAuth flows

MooPiew separates SCB tokens by purpose. Owner/profile authorization uses the
authorization-code flow: SCB returns a one-time code to the registered HTTPS
callback and the server exchanges it at `/v1/oauth/token`; this encrypted token
is not reused as a merchant payment credential. Merchant payment APIs use the
separate `SCB_PAYMENT_OAUTH_MODE` (normally `client_credentials`) service token.
Generate a fresh `requestUId` for every SCB request. If the SCB product supports
a caller-supplied state parameter, enable and validate it before exchanging the
authorization code.

The `/v1/oauth/token/refresh` endpoint renews the stored authorization token.
Do not place access tokens, refresh tokens or authorization codes in
`.env.payment`; store them encrypted server-side and never expose them to the
browser.

For SCB EASY Deeplink payments, use the transaction identifier returned when
creating the transaction with `GET /v2/transactions/{transactionId}` as a
fallback status inquiry after the payment confirmation callback.
