from fastapi import APIRouter, Request, Query, HTTPException
from typing import List, Dict, Any
import numpy as np
from datetime import datetime

router = APIRouter()

@router.get("/compare")
async def get_comparison_data(
    request: Request,
    symbols: str = Query(..., description="Comma-separated list of symbols"),
    interval: str = Query("1m", pattern="^1m$"),
    limit: int = Query(200, ge=1, le=1000)
):
    symbol_list = [s.strip() for s in symbols.split(",") if s.strip()]

    if len(symbol_list) > 6:
        raise HTTPException(status_code=400, detail="Maximum 6 symbols allowed")

    if not symbol_list:
        raise HTTPException(status_code=400, detail="At least one symbol required")

    db = request.app.state.db

    # We might need to limit the total number of buckets to avoid pulling too much data
    # If we want 200 buckets per symbol, but they are aligned, we can just limit the number of buckets.
    # To get exactly 'limit' buckets, we can find the distinct buckets first.

    bucket_query = """
        SELECT DISTINCT time_bucket('1 minute', time) AS bucket
        FROM orderbook_metrics
        WHERE symbol = ANY($1)
        ORDER BY bucket DESC
        LIMIT $2
    """

    buckets_rows = await db.fetch(bucket_query, symbol_list, limit)
    if not buckets_rows:
        return {s: [] for s in symbol_list}

    target_buckets = [row["bucket"] for row in buckets_rows]
    min_bucket = target_buckets[-1]
    max_bucket = target_buckets[0]

    # Now get the data for these buckets
    data_query = """
        SELECT
            time_bucket('1 minute', time) AS bucket,
            symbol,
            avg(imbalance_ratio) AS imbalance_ratio,
            avg(spread_bps) AS spread_bps
        FROM orderbook_metrics
        WHERE symbol = ANY($1) AND time >= $2 AND time <= $3
        GROUP BY bucket, symbol
        ORDER BY bucket DESC
    """

    rows = await db.fetch(data_query, symbol_list, min_bucket, max_bucket)

    # Organize data by bucket and symbol
    # bucket_map[timestamp][symbol] = data
    bucket_map = {bucket: {} for bucket in target_buckets}
    for row in rows:
        b = row["bucket"]
        if b in bucket_map:
            bucket_map[b][row["symbol"]] = {
                "time": b,
                "imbalance_ratio": row["imbalance_ratio"],
                "spread_bps": row["spread_bps"]
            }

    # Align data
    result = {symbol: [] for symbol in symbol_list}
    # We iterate in chronological order for the frontend
    for bucket in reversed(target_buckets):
        for symbol in symbol_list:
            if symbol in bucket_map[bucket]:
                result[symbol].append(bucket_map[bucket][symbol])
            else:
                # Provide null entry for alignment
                result[symbol].append({
                    "time": bucket,
                    "imbalance_ratio": None,
                    "spread_bps": None
                })

    return result
