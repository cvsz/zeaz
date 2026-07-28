# Security Review

Reviewed 2026-07-28. Secrets are environment-only, ignored, and should be mode
0600; `scripts/production-check.sh` rejects symlinks, ownership mismatches, and
group/world access. Admin credentials use UTF-8-safe `X-Admin-Key-B64`; public endpoints do
not expose provider keys. SCB callbacks require a configured HMAC secret and
valid signature when SCB is enabled. The authorization-code flow validates
atomically consumed, expiring callback state. Optional PKCE uses an S256
challenge and an encrypted one-time verifier; keep it disabled until the
approved SCB product contract and Sandbox UAT confirm the token field.
Onboarding documents are stored only as Fernet ciphertext using the dedicated
`DOCUMENT_ENCRYPTION_KEY`; plaintext migration verifies the recorded SHA-256
before replacement. Do not reuse payment, admin, or backup keys.

CI runs CodeQL, Python runtime and full npm dependency audits,
parameterized-SQL regression coverage, and CSP/security-header checks. Current
CodeQL and vulnerability status must be read from CI evidence; this document
does not assert zero findings. Rotate any credential that has appeared in logs,
shell history, or shared files.

The engineering dashboard is operational telemetry, not a public endpoint.
Terraform restricts Cloudflare Access to an explicit, nonempty set of exact
operator emails; `everyone` and domain-wide rules are prohibited. Caddy Basic
Auth provides independent origin enforcement using credentials stored only in
the mode-`0600` ignored `.env.dashboard` file. The Caddy systemd unit must not
use `--environ`, which would write those credentials to the service journal.

SCB callback claims never settle an order by themselves; the server performs a
provider inquiry first. A provider-confirmed payment received after an order
was cancelled is recorded as a paid payment attempt without reopening the
order, and emits `payment_received_cancelled_order` with
`requires_reconciliation=true` for operator refund/reconciliation.

Forwarded client IP headers are ignored by default. Enable
`TRUST_CF_CONNECTING_IP` only when direct application access is prevented and
the loopback proxy chain is the sole caller; otherwise local header spoofing can
invalidate per-client rate limits.
