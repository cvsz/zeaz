# zTrader Consolidation Status

Date: 2026-09-12
Lifecycle: MIGRATION_SOURCE
Scope: apps/ztrader

This repository/path is retained as a migration source. New independent trading-platform capabilities should be implemented in the canonical owner instead of extending this duplicate runtime.

## Preserve and migrate

- unique tested zTrader features
- exchange/service adapters
- portfolio/websocket patterns

## Canonical destinations

- intelligence -> cvsz/zworkforce
- execution/risk/paper -> cvsz/zksato
- UI -> cvsz/zdash
- model routing -> cvsz/zaiman

## Retirement gates

- feature inventory complete
- source/destination parity matrix complete
- tests migrated or explicitly retired
- no production runtime references remain
- CI green
- rollback path documented
- explicit archive approval

No implementation is deleted by this marker. Live-money automation is not authorized.

`cvsz/zsme` is explicitly excluded from this program and must not be inspected or modified.
