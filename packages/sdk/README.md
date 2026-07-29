# @moopiew/sdk

Typed client for the deployed MooPiew API. It supports storefront, onboarding,
orders, SCB QR, delivery quotes and tracking, monitoring, documents, owner
dashboard, operations, and provider-backed AI. Mutating requests are never
retried automatically, preventing accidental duplicate business operations.

The `ai` service exposes the owner-only live provider configuration, model
catalog and chat endpoints. Each call accepts the owner key explicitly so the
SDK does not retain it or place it in URLs or browser storage.

The `admin`, `operations`, and `documents` services use the same explicit-key
boundary. Receipt printing uses the SDK text-response path while all other
services parse the production JSON contracts.
