# Integrations

The current integration is the same-origin MooPiew operations API. It is
read-only in zERP and is authenticated with the existing owner API contract.
Future adapters (identity, payments, messaging, object storage, AI, and
accounting exports) require signed payload contracts, replay protection,
idempotency, delivery logs, and reconciliation tests before implementation.
