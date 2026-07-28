# Provider rotation hooks

`rotate-provider-secrets.sh` is dry-run by default. Provider revocation and
new-key creation must be implemented here as small, reviewed executable hooks.

Hooks must:

- call the provider's official revoke/create API or CLI;
- update the deployment secret store atomically (never print values);
- leave a credential-free audit record under `ROTATION_OUT_DIR`;
- exit non-zero when revocation or replacement fails;
- avoid putting credentials in command-line arguments or Git.

Run only after reviewing the inventory:

```bash
./scripts/rotate-provider-secrets.sh
ROTATION_APPROVED=YES ./scripts/rotate-provider-secrets.sh --execute
```

The repository intentionally does not ship generic provider revocation calls:
AI, payment, Cloudflare, GitHub, AWS and SCB credentials have different scopes
and irreversible side effects. Add one hook per approved provider/account.
