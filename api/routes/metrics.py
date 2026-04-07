from fastapi import APIRouter, Request, Query
from typing import List, Dict, Any
from datetime import datetime

router = APIRouter()

@router.get("/metrics/{symbol}", response_model=List[Dict[str, Any]])
async def get_historical_metrics(
    symbol: str,
    request: Request,
    interval: str = Query("1m", pattern="^1m$"), # For now only 1m as per requirements
    limit: int = Query(200, ge=1, le=1000)
):
    """
    Historical imbalance time series for a symbol.
    Returns [{time, imbalance_ratio, spread_bps, mid_price}] array.
    TimescaleDB query uses time_bucket('1 minute', time) for aggregation.
    """
    db = request.app.state.db

    # Using time_bucket for aggregation as requested.
    # We'll take the average for the other metrics within the bucket.
    query = """
        SELECT
            time_bucket('1 minute', time) AS bucket,
            avg(imbalance_ratio) AS imbalance_ratio,
            avg(spread_bps) AS spread_bps,
            avg(mid_price) AS mid_price
        FROM orderbook_metrics
        WHERE symbol = $1
        GROUP BY bucket
        ORDER BY bucket DESC
        LIMIT $2
    """
    rows = await db.fetch(query, symbol, limit)

    return [
        {
            "time": row["bucket"],
            "imbalance_ratio": row["imbalance_ratio"],
            "spread_bps": row["spread_bps"],
            "mid_price": row["mid_price"]
        } for row in rows
    ]

@router.get("/metrics/{symbol}/summary", response_model=Dict[str, Any])
async def get_metrics_summary(symbol: str, request: Request):
    """Current spread, imbalance, depth levels for a symbol."""
    db = request.app.state.db
    query = """
        SELECT * FROM orderbook_metrics
        WHERE symbol = $1
        ORDER BY time DESC
        LIMIT 1
    """
    row = await db.fetchrow(query, symbol)
    if not row:
        return {}

    return dict(row)

@router.get("/leaderboard", response_model=List[Dict[str, Any]])
async def get_leaderboard(request: Request):
    """Symbols ranked by avg imbalance magnitude (last 1h)."""
    db = request.app.state.db
    query = """
        SELECT
            symbol,
            avg(abs(imbalance_ratio)) AS avg_imbalance_magnitude
        FROM orderbook_metrics
        WHERE time >= now() - INTERVAL '1 hour'
        GROUP BY symbol
        ORDER BY avg_imbalance_magnitude DESC
    """
    rows = await db.fetch(query)
    return [dict(row) for row in rows]
