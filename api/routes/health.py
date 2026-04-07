import time
from fastapi import APIRouter, Request
from typing import Dict, Any

router = APIRouter()

@router.get("/health", response_model=Dict[str, Any])
async def health_check(request: Request):
    """
    Check status of DB and Redis connections.
    Calculate collector_lag_ms based on the latest record in orderbook_metrics.
    """
    db_connected = False
    redis_connected = False
    collector_lag_ms = None

    # Check DB
    try:
        db = request.app.state.db
        await db.execute("SELECT 1")
        db_connected = True
    except Exception:
        pass

    # Check Redis
    try:
        redis = request.app.state.redis
        await redis.ping()
        redis_connected = True
    except Exception:
        pass

    # Calculate collector lag
    if db_connected:
        try:
            row = await db.fetchrow("SELECT MAX(time) AS last_ts FROM orderbook_metrics")
            if row and row["last_ts"]:
                last_ts = row["last_ts"]
                now = time.time()
                collector_lag_ms = int((now - last_ts.timestamp()) * 1000)
        except Exception:
            pass

    return {
        "status": "healthy" if db_connected and redis_connected else "unhealthy",
        "db_connected": db_connected,
        "redis_connected": redis_connected,
        "collector_lag_ms": collector_lag_ms
    }
