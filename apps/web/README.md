# @moopiew/web

Production React/Vite multi-page application for every MooPiew browser surface:
storefront, onboarding, monitoring, owner AI, owner dashboard, operations, and
document intake/policy administration. All application data flows through
`@moopiew/sdk` to the Python service; browser state is never a second source of
truth.

Set `VITE_API_URL=https://moopiew.zeaz.dev` only when running the application on
a different origin. Owner keys, document contents, and AI conversations remain
in component memory and are never persisted in browser storage or URLs.

Build and publish the exact static artifact set with:

```bash
npm run build
npm run publish:platform
```
