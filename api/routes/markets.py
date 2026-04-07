from fastapi import APIRouter, Request
from typing import List

router = APIRouter()

@router.get("/markets", response_model=List[str])
async def get_markets(request: Request):
    """List all available symbols from orderbook_metrics."""
    db = request.app.state.db
    rows = await db.fetch("SELECT DISTINCT symbol FROM orderbook_metrics ORDER BY symbol")
    return [row["symbol"] for row in rows]
