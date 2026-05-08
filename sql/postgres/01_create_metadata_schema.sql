CREATE TABLE IF NOT EXISTS query_log (
    id SERIAL PRIMARY KEY,
    query_text TEXT NOT NULL,
    query_hash VARCHAR(64) NOT NULL,
    complexity VARCHAR(20),
    warehouse_used VARCHAR(50) NOT NULL,
    warehouse_size VARCHAR(10) NOT NULL,
    estimated_cost NUMERIC(10, 6),
    actual_cost NUMERIC(10, 6),
    latency_ms INTEGER,
    rows_returned INTEGER,
    status VARCHAR(20) DEFAULT 'success',
    error_message TEXT,
    executed_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS warehouse_stats (
    id SERIAL PRIMARY KEY,
    warehouse_name VARCHAR(50) NOT NULL,
    warehouse_size VARCHAR(10) NOT NULL,
    credits_per_hour NUMERIC(10, 4) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    recorded_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_query_log_hash_warehouse
    ON query_log (query_hash, warehouse_size);

CREATE INDEX IF NOT EXISTS idx_query_log_executed_at
    ON query_log (executed_at);

CREATE TABLE IF NOT EXISTS query_performance_history (
    query_hash      TEXT        NOT NULL,
    warehouse_size  TEXT        NOT NULL,
    avg_latency_s   FLOAT       NOT NULL DEFAULT 0.0,
    avg_cost        FLOAT       NOT NULL DEFAULT 0.0,
    sample_count    INTEGER     NOT NULL DEFAULT 0,
    last_updated    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (query_hash, warehouse_size)
);