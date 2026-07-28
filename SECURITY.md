# Security Review

Reviewed 2026-07-28. Secrets are environment-only, ignored, and should be mode
0600; `scripts/production-check.sh` rejects symlinks, ownership mismatches, and
group/world access. Admin credentials use UTF-8-safe `X-Admin-Key-B64`; public endpoints do
not expose provider keys. SCB callbacks require a configured HMAC secret and
valid signature when SCB is enabled. The authorization-code flow validates
atomically consumed, expiring callback state. Optional PKCE uses an S256
challenge and an encrypted one-time verifier; keep it disabled until the
approved SCB product contract and Sandbox UAT confirm the token field.

CI runs CodeQL, Python runtime and full npm dependency audits,
parameterized-SQL regression coverage, and CSP/security-header checks. Current
CodeQL and vulnerability status must be read from CI evidence; this document
does not assert zero findings. Rotate any credential that has appeared in logs,
shell history, or shared files.

Forwarded client IP headers are ignored by default. Enable
`TRUST_CF_CONNECTING_IP` only when direct application access is prevented and
the loopback proxy chain is the sole caller; otherwise local header spoofing can
invalidate per-client rate limits.
