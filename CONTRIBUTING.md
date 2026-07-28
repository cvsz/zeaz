# Contributing to MooPiew

Keep changes small, test the affected customer and owner flow, and update the
API/operations documentation when behaviour changes. Never commit populated
environment files, databases, backup archives, certificates, payment material,
QR images or customer data.

Before opening a pull request, run:

```bash
python3 -m py_compile app.py
./scripts/ci/test.sh
```

Use the pull-request template to record workflow, migration and security impact.
For a vulnerability or exposed secret, do not open a public issue; follow
[`docs/security.th.md`](docs/security.th.md) and rotate the affected secret.
