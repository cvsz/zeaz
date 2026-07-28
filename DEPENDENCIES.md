# Dependencies

Dependency declarations are authoritative in:

- Python runtime: `requirements.txt`
- Python validation and test tooling: `requirements-dev.txt`
- Node workspace: `package.json`, workspace `package.json` files, and
  `package-lock.json`
- Terraform: `infrastructure/terraform/cloudflare/.terraform.lock.hcl`
- Container runtime: `dashboard/Dockerfile`
- Kubernetes validation: pinned Kustomize and kubeconform versions and release
  checksums in `scripts/ci/install-kubernetes-tools.sh`

PyYAML is validation-only: it parses the OpenAPI contract so CI can reject
invalid YAML, broken local references, incomplete protected-route security
metadata, and published operations that the isolated application does not
recognize. It is deliberately excluded from the application container.

CI runs `pip check`, a strict `pip-audit` scan of runtime requirements, and
`npm audit --audit-level=moderate` across runtime and development dependencies.
SBOM generation and artifact signing remain open production-readiness controls.
