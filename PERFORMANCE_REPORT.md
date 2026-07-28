# Performance Review

SQLite WAL and indexed order/payment/delivery lookups are enabled. Production health checks use bounded retries. AI catalog calls are cached and AI fallback is bounded by the live catalog; provider timeouts remain the principal latency risk and should be measured with production credentials before raising limits.

Isolated benchmark (`scripts/benchmark.sh`, 20 loopback `/api/health` requests): mean 0.0024s, p95 0.0046s, max 0.0084s.
