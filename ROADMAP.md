# Roadmap

- Raise branch-focused coverage for critical `app.py` mutations beyond the
  current 50.88% line baseline, prioritizing inventory, recipe and settings
  mutation error paths. The repository-wide enforced floor is 52%.
- Migrate the Cloudflare Terraform state from the local operator host to an
  encrypted, locking remote backend with documented bootstrap and recovery.
