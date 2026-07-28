# Performance Review

SQLite WAL and indexed order/payment/delivery lookups are enabled. Production health checks use bounded retries. AI catalog calls are cached and AI fallback is bounded by the live catalog; provider timeouts remain the principal latency risk and should be measured with production credentials before raising limits.
