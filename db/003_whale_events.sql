-- 003_whale_events.sql
-- Table for storing whale and iceberg order events

CREATE TABLE IF NOT EXISTS whale_events (
    time            TIMESTAMPTZ       NOT NULL,
    symbol          TEXT              NOT NULL,
    price           DOUBLE PRECISION  NOT NULL,
    size_usd        DOUBLE PRECISION  NOT NULL,
    type            TEXT              NOT NULL, -- whale_bid, whale_ask, iceberg
    persisted_ticks INTEGER           DEFAULT 1
);

-- Convert to hypertable with 1-hour chunks
SELECT create_hypertable('whale_events', 'time', chunk_time_interval => INTERVAL '1 hour', if_not_exists => TRUE);

-- Create index for symbol-based queries
CREATE INDEX IF NOT EXISTS idx_whale_events_symbol_time ON whale_events (symbol, time DESC);
