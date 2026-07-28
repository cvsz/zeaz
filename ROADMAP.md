# Roadmap

- Raise branch-focused coverage for critical `app.py` mutations beyond the
  current 52.89% line baseline, prioritizing menu, delivery-pricing and coupon
  mutation concurrency/error paths. The repository-wide enforced floor is 53%.
- Migrate the Cloudflare Terraform state from the local operator host to an
  encrypted, locking remote backend with documented bootstrap and recovery.
