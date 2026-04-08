from fastapi import APIRouter, Request, Query
from typing import List, Dict, Any
from datetime import datetime, timezone

router = APIRouter()

@router.get("/signals", response_model=List[Dict[str, Any]])
async def get_active_signals(
    request: Request,
    symbol: str = Query(None),
    min_confidence: float = Query(50, ge=0, le=100)
):
    """
    Get active trade signals.
    Hides stale signals (expires_at < now).
    """
    db = request.app.state.db

    query = """
        SELECT * FROM signals
        WHERE expires_at > $1 AND confidence >= $2
    """
    params = [datetime.now(timezone.utc), min_confidence]

    if symbol:
        query += " AND symbol = $3"
        params.append(symbol)

    query += " ORDER BY time DESC LIMIT 50"

    rows = await db.fetch(query, *params)

    return [dict(row) for row in rows]
