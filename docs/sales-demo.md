# zTTShop ERP + AI Sales Demo

The customer-facing demonstration is published at:

`https://zttshop.zeaz.dev/demo`

The `/demo` path redirects to the generated React entry at
`/platform/sales-demo.html`. It is intentionally isolated from the MooPiew
restaurant storefront and owner operations API.

## Demo scope

- Central command center for Facebook Messenger and Shopee
- Deterministic AI Sales Bot scenarios for the serum product
- Product knowledge view for eight extracts and pain-point mapping
- Simulated order creation, COD summary, and stock decrement
- Human handoff guardrail when a customer requests an agent

All customer messages, orders, channel states, and stock values are demo data.
The page does not call Shopee, Facebook, payment, or production order APIs.

## Source and publishing

The source of truth is:

- `apps/web/sales-demo.html`
- `apps/web/src/sales-demo.tsx`
- `apps/web/src/sales-demo.css`
- `app.py` host-routed `/demo` alias

Build and publish the static platform artifact with:

```bash
npm --workspace @moopiew/web run build
npm run publish:platform
```

Real channel connectors, webhook verification, idempotency, and transactional
inventory synchronization remain a separate production integration phase.
