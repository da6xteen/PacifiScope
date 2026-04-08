-- 004_signals.sql
-- Table for storing trade signals

CREATE TABLE IF NOT EXISTS signals (
    time            TIMESTAMPTZ       NOT NULL,
    symbol          TEXT              NOT NULL,
    direction       TEXT              NOT NULL, -- LONG, SHORT
    confidence      DOUBLE PRECISION  NOT NULL,
    rules_fired     TEXT[]            NOT NULL,
    expires_at      TIMESTAMPTZ       NOT NULL
);

-- Convert to hypertable
SELECT create_hypertable('signals', 'time', chunk_time_interval => INTERVAL '1 hour', if_not_exists => TRUE);

-- Index for querying active signals
CREATE INDEX IF NOT EXISTS idx_signals_symbol_time ON signals (symbol, time DESC);
CREATE INDEX IF NOT EXISTS idx_signals_expires_at ON signals (expires_at);
