import json
import numpy as np
from fastapi import APIRouter, Request, Query
from typing import List, Dict, Any
from datetime import datetime, timedelta

router = APIRouter()

CACHE_TTL = 300  # 5 minutes

@router.get("/correlation/{symbol}")
async def get_correlation(
    symbol: str,
    request: Request,
    days: int = Query(7, ge=1, le=30)
):
    """
    Correlation between imbalance_ratio (t) and price_change (t+5min).
    Returns scatter data and correlation metrics.
    """
    redis = request.app.state.redis
    db = request.app.state.db
    cache_key = f"analysis:correlation:{symbol}:{days}"

    # Try cache
    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)

    # Query metrics bucketed by 1 minute
    # We join orderbook_metrics with itself with a 5 minute offset
    query = """
        WITH bucketed AS (
            SELECT
                time_bucket('1 minute', time) AS bucket,
                avg(imbalance_ratio) as imbalance,
                avg(mid_price) as price
            FROM orderbook_metrics
            WHERE symbol = $1 AND time >= now() - ($2 * INTERVAL '1 day')
            GROUP BY bucket
        )
        SELECT
            t1.imbalance as imbalance_t0,
            ((t2.price - t1.price) / t1.price) * 10000 as price_change_bps
        FROM bucketed t1
        JOIN bucketed t2 ON t2.bucket = t1.bucket + INTERVAL '5 minutes'
        WHERE t1.price > 0
    """
    rows = await db.fetch(query, symbol, days)

    if not rows:
        return {
            "symbol": symbol,
            "correlation": 0,
            "r_squared": 0,
            "sample_size": 0,
            "data": []
        }

    imbalances = np.array([row["imbalance_t0"] for row in rows])
    price_changes = np.array([row["price_change_bps"] for row in rows])

    # Pearson correlation
    correlation = np.corrcoef(imbalances, price_changes)[0, 1]
    if np.isnan(correlation):
        correlation = 0

    r_squared = correlation ** 2

    # Prepare scatter data (limit to 1000 points for frontend performance)
    # We sample if there are too many points
    data = []
    step = max(1, len(rows) // 1000)
    for i in range(0, len(rows), step):
        row = rows[i]
        data.append({
            "x": round(row["imbalance_t0"], 4),
            "y": round(row["price_change_bps"], 2)
        })

    result = {
        "symbol": symbol,
        "correlation": round(float(correlation), 4),
        "r_squared": round(float(r_squared), 4),
        "sample_size": len(rows),
        "data": data
    }

    # Cache result
    await redis.setex(cache_key, CACHE_TTL, json.dumps(result))

    return result

@router.get("/heatmap/{symbol}")
async def get_heatmap(
    symbol: str,
    request: Request
):
    """
    Hourly average imbalance grid (Day of Week x Hour of Day).
    Returns a 14x24 grid (for last 14 days, wait, prompt says 14x24 grid,
    but usually heatmap by hour of day x day of week is 7x24).
    Let me re-read: "Heatmap of avg imbalance by hour-of-day x day-of-week (14x24 grid)"
    Maybe it means 2 weeks? Or maybe 7 days x 24 hours?
    Wait, 14x24 would be 14 days. Let's stick to 14x24 as requested.
    """
    redis = request.app.state.redis
    db = request.app.state.db
    cache_key = f"analysis:heatmap:{symbol}"

    # Try cache
    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)

    # Query for last 14 days
    query = """
        SELECT
            EXTRACT(DOW FROM time) as dow,
            EXTRACT(HOUR FROM time) as hour,
            DATE_TRUNC('day', time) as date,
            avg(imbalance_ratio) as avg_imbalance
        FROM orderbook_metrics
        WHERE symbol = $1 AND time >= now() - INTERVAL '14 days'
        GROUP BY date, dow, hour
        ORDER BY date DESC, hour ASC
    """
    rows = await db.fetch(query, symbol)

    # Format into grid
    # We'll return a list of objects {date, dow, hour, value}
    grid = []
    for row in rows:
        grid.append({
            "date": row["date"].strftime("%Y-%m-%d"),
            "dow": int(row["dow"]),
            "hour": int(row["hour"]),
            "value": round(row["avg_imbalance"], 4)
        })

    result = {
        "symbol": symbol,
        "grid": grid
    }

    # Cache result
    await redis.setex(cache_key, CACHE_TTL, json.dumps(result))

    return result
