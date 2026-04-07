-- 001_initial_schema.sql
-- Initial schema for PacifiScope orderbook imbalance analytics

-- Enable TimescaleDB extension if not already enabled
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Create orderbook table
CREATE TABLE IF NOT EXISTS orderbook_imbalance (
    time        TIMESTAMPTZ       NOT NULL,
    symbol      TEXT              NOT NULL,
    bid_depth   DOUBLE PRECISION  NOT NULL,
    ask_depth   DOUBLE PRECISION  NOT NULL,
    imbalance   DOUBLE PRECISION  NOT NULL
);

-- Convert to hypertable for time-series optimization
SELECT create_hypertable('orderbook_imbalance', 'time', if_not_exists => TRUE);

-- Create index for symbol-based queries
CREATE INDEX IF NOT EXISTS idx_symbol_time ON orderbook_imbalance (symbol, time DESC);
