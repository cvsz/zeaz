# Security Review

Reviewed 2026-07-28. Secrets are environment-only, ignored, and should be mode 0600. Admin credentials use UTF-8-safe `X-Admin-Key-B64`; public endpoints do not expose provider keys. SCB callbacks now require a configured HMAC secret and valid signature when SCB is enabled. Keep OAuth callback state/PKCE enabled in the SCB integration before production authorization-code use.

Quality checks: CodeQL alerts 0, dependency audit clean, parameterized SQL, CSP/security headers enabled. Rotate any credential that has appeared in logs, shell history, or shared files.
