import os
import asyncpg
from unittest.mock import AsyncMock
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from redis.asyncio import Redis
from routes import markets, metrics, ws, health
from contextlib import asynccontextmanager

# Setup database and redis connection strings
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@timescaledb:5432/pacifiscope")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # On startup: Create DB pool and Redis client
    if not hasattr(app.state, "db"):
        app.state.db = await asyncpg.create_pool(DATABASE_URL)
    if not hasattr(app.state, "redis"):
        app.state.redis = Redis.from_url(REDIS_URL, decode_responses=False)
    yield
    # On shutdown: Close connections
    if hasattr(app.state, "db") and app.state.db:
        # Check if it's a mock or real pool
        if hasattr(app.state.db, "close") and not isinstance(app.state.db, AsyncMock):
            await app.state.db.close()
    if hasattr(app.state, "redis") and app.state.redis:
        if hasattr(app.state.redis, "close") and not isinstance(app.state.redis, AsyncMock):
            await app.state.redis.close()

app = FastAPI(title="PacifiScope API", lifespan=lifespan)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict to frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to PacifiScope API"}

# Include routers
app.include_router(markets.router, prefix="/api", tags=["markets"])
app.include_router(metrics.router, prefix="/api", tags=["metrics"])
app.include_router(health.router, tags=["health"])
app.include_router(ws.router, prefix="/ws", tags=["websocket"])
