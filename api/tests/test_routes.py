import pytest
import json
import gzip
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from datetime import datetime, timezone
from main import app

@pytest.fixture(autouse=True)
def setup_mocks():
    app.state.db = AsyncMock()
    app.state.redis = AsyncMock()
    yield

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

def test_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to PacifiScope API"}

def test_get_markets(client):
    mock_db = app.state.db
    mock_db.fetch.return_value = [{"symbol": "BTC-USD"}, {"symbol": "ETH-USD"}]

    response = client.get("/api/markets")
    assert response.status_code == 200
    assert response.json() == ["BTC-USD", "ETH-USD"]

def test_get_historical_metrics(client):
    mock_db = app.state.db
    now = datetime.now(timezone.utc)
    mock_db.fetch.return_value = [
        {"bucket": now, "imbalance_ratio": 0.5, "spread_bps": 2.0, "mid_price": 50000.0}
    ]

    response = client.get("/api/metrics/BTC-USD?interval=1m&limit=10")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["imbalance_ratio"] == 0.5

def test_get_metrics_summary(client):
    mock_db = app.state.db
    mock_db.fetchrow.return_value = {
        "symbol": "BTC-USD",
        "imbalance_ratio": 0.5,
        "spread_bps": 2.0,
        "mid_price": 50000.0,
        "depth_5bps": 100.0,
        "depth_10bps": 200.0,
        "depth_25bps": 500.0,
        "depth_50bps": 1000.0,
        "price_pressure": 0.1,
        "time": datetime.now(timezone.utc)
    }

    response = client.get("/api/metrics/BTC-USD/summary")
    assert response.status_code == 200
    assert response.json()["symbol"] == "BTC-USD"

def test_get_leaderboard(client):
    mock_db = app.state.db
    mock_db.fetch.return_value = [
        {"symbol": "BTC-USD", "avg_imbalance_magnitude": 0.8},
        {"symbol": "ETH-USD", "avg_imbalance_magnitude": 0.4}
    ]

    response = client.get("/api/leaderboard")
    assert response.status_code == 200
    assert len(response.json()) == 2

def test_health_check(client):
    mock_db = app.state.db
    mock_redis = app.state.redis
    mock_db.execute.return_value = None
    mock_redis.ping.return_value = True
    mock_db.fetchrow.return_value = {"last_ts": datetime.now(timezone.utc)}

    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

@pytest.mark.asyncio
async def test_websocket_relay_gzipped():
    mock_redis = AsyncMock()
    app.state.redis = mock_redis
    app.state.db = AsyncMock()

    pubsub = AsyncMock()
    mock_redis.pubsub.return_value = pubsub

    test_data = {"symbol": "BTC-USD", "ts": 123456789}
    compressed_data = gzip.compress(json.dumps(test_data).encode("utf-8"))

    async def mock_listen():
        yield {"type": "message", "data": compressed_data}
        await asyncio.sleep(0.1)

    pubsub.listen.return_value = mock_listen()

    with TestClient(app) as client:
        with client.websocket_connect("/ws/live/BTC-USD") as websocket:
            data = websocket.receive_json()
            assert data["symbol"] == "BTC-USD"

@pytest.mark.asyncio
async def test_websocket_relay_plain():
    mock_redis = AsyncMock()
    app.state.redis = mock_redis
    app.state.db = AsyncMock()

    pubsub = AsyncMock()
    mock_redis.pubsub.return_value = pubsub

    test_data = {"symbol": "ETH-USD", "ts": 987654321}
    plain_data = json.dumps(test_data).encode("utf-8")

    async def mock_listen():
        yield {"type": "message", "data": plain_data}
        await asyncio.sleep(0.1)

    pubsub.listen.return_value = mock_listen()

    with TestClient(app) as client:
        with client.websocket_connect("/ws/live/ETH-USD") as websocket:
            data = websocket.receive_json()
            assert data["symbol"] == "ETH-USD"
