# Security

- Protected data is requested only after an owner key is supplied.
- The key is sent as `X-Admin-Key-B64` and kept in component state.
- No customer address, phone number, payment credential, or AI provider key is
  copied into zERP state beyond the API response required for the current view.
- Caddy/Tunnel is the only public boundary; port 3001 is loopback-only.
- Database, uploaded documents, `.env*` files, and provider credentials stay
  outside generated browser assets.
- Any new mutation requires server-side authorization, validation, an audit
  record, and a regression test before it is exposed in zERP.

This document is an implementation control, not a claim of legal or tax
compliance. Thai accounting and PDPA decisions require business review.
