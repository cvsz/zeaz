# Configuration

Only non-secret browser configuration is supported today:

| Variable | Purpose | Safe default |
| --- | --- | --- |
| `VITE_API_URL` | MooPiew API origin | same origin |
| `ZERP_PORT` | local operator port | `3001` |
| `ZERP_PUBLIC_HOST` | allowed preview host | `zerp.zeaz.dev` |

Owner credentials are entered at runtime and are never placed in `.env`, the
URL, local storage, generated assets, or logs. Server-side provider and
database credentials belong to the MooPiew deployment environment.
