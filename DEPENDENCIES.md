# Dependencies

Dependency declarations are authoritative in:

- Python runtime: `requirements.txt`
- Node workspace: `package.json`, workspace `package.json` files, and
  `package-lock.json`
- Terraform: `infrastructure/terraform/cloudflare/.terraform.lock.hcl`
- Container runtime: `dashboard/Dockerfile`

CI currently runs `npm audit --omit=dev --audit-level=high` and `pip check`.
These do not constitute a complete vulnerability assessment: Python
vulnerability scanning, development-dependency scanning, SBOM generation, and
artifact signing remain open production-readiness controls.
