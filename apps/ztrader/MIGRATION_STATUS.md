# zTrader Migration Status

`apps/ztrader` is a duplicate implementation being consolidated into canonical services.

Destinations:
- intelligence/agents -> `cvsz/zworkforce`
- paper/execution/risk/reconciliation -> `cvsz/zksato`
- dashboard/UI -> `cvsz/zdash`
- model/provider routing -> `cvsz/zaiman`

Only unique, tested behavior should be migrated. Do not delete this tree until parity tests pass and runtime references are removed.

Explicit exclusion: `cvsz/zsme` is not part of this program.
