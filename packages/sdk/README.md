# @moopiew/sdk

Typed, fetch-based client for the deployed MooPiew API. It supports the public
storefront menu, create/lookup/cancel order flow, SCB QR creation, delivery
quotes/tracking and the SCB payment configuration endpoint. Mutating requests
are never retried automatically, preventing accidental duplicate orders.
