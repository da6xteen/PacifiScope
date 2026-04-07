-- 002_orderbook_metrics.sql
-- Metrics for orderbook imbalance analytics

-- Create orderbook_metrics table
CREATE TABLE IF NOT EXISTS orderbook_metrics (
    time            TIMESTAMPTZ       NOT NULL,
    symbol          TEXT              NOT NULL,
    imbalance_ratio DOUBLE PRECISION  NOT NULL,
    spread_bps      DOUBLE PRECISION  NOT NULL,
    depth_5bps      DOUBLE PRECISION  NOT NULL,
    depth_10bps     DOUBLE PRECISION  NOT NULL,
    depth_25bps     DOUBLE PRECISION  NOT NULL,
    depth_50bps     DOUBLE PRECISION  NOT NULL,
    price_pressure  DOUBLE PRECISION  NOT NULL,
    mid_price       DOUBLE PRECISION  NOT NULL
);

-- Convert to hypertable with 1-hour chunks
SELECT create_hypertable('orderbook_metrics', 'time', chunk_time_interval => INTERVAL '1 hour', if_not_exists => TRUE);

-- Create index for symbol-based queries
CREATE INDEX IF NOT EXISTS idx_metrics_symbol_time ON orderbook_metrics (symbol, time DESC);

-- Continuous aggregate for 1-minute OHLC of imbalance_ratio
CREATE MATERIALIZED VIEW IF NOT EXISTS imbalance_ohlc_1m
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 minute', time) AS bucket,
    symbol,
    first(imbalance_ratio, time) AS open,
    max(imbalance_ratio) AS high,
    min(imbalance_ratio) AS low,
    last(imbalance_ratio, time) AS close
FROM orderbook_metrics
GROUP BY bucket, symbol;

-- Refresh policy for the continuous aggregate
SELECT add_continuous_aggregate_policy('imbalance_ohlc_1m',
    start_offset => INTERVAL '2 hours',
    end_offset => INTERVAL '1 minute',
    schedule_interval => INTERVAL '1 minute');
