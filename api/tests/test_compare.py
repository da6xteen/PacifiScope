import pytest
from unittest.mock import AsyncMock
from fastapi.testclient import TestClient
from datetime import datetime, timezone, timedelta
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

def test_compare_limit_exceeded(client):
    symbols = "BTC,ETH,SOL,XRP,ADA,DOT,LINK"
    response = client.get(f"/api/compare?symbols={symbols}")
    assert response.status_code == 400
    assert response.json()["detail"] == "Maximum 6 symbols allowed"

def test_compare_no_symbols(client):
    response = client.get("/api/compare?symbols=")
    assert response.status_code == 400
    assert response.json()["detail"] == "At least one symbol required"

def test_compare_success(client):
    mock_db = app.state.db
    now = datetime.now(timezone.utc).replace(second=0, microsecond=0)
    bucket1 = now
    bucket2 = now - timedelta(minutes=1)

    # Mock bucket query
    mock_db.fetch.side_effect = [
        # First call: bucket_query
        [{"bucket": bucket1}, {"bucket": bucket2}],
        # Second call: data_query
        [
            {"bucket": bucket1, "symbol": "BTC", "imbalance_ratio": 0.5, "spread_bps": 1.0},
            {"bucket": bucket1, "symbol": "ETH", "imbalance_ratio": -0.2, "spread_bps": 2.0},
            {"bucket": bucket2, "symbol": "BTC", "imbalance_ratio": 0.4, "spread_bps": 1.1},
            # ETH missing for bucket2
        ]
    ]

    response = client.get("/api/compare?symbols=BTC,ETH&limit=2")
    assert response.status_code == 200
    data = response.json()

    assert "BTC" in data
    assert "ETH" in data
    assert len(data["BTC"]) == 2
    assert len(data["ETH"]) == 2

    # Check alignment (chronological order)
    def to_iso(dt):
        return dt.isoformat().replace("+00:00", "+00:00") # FastAPI/JSON default behavior seen in failure

    assert data["BTC"][0]["time"] == bucket2.isoformat()
    assert data["BTC"][1]["time"] == bucket1.isoformat()

    assert data["BTC"][1]["imbalance_ratio"] == 0.5
    assert data["ETH"][1]["imbalance_ratio"] == -0.2

    assert data["BTC"][0]["imbalance_ratio"] == 0.4
    assert data["ETH"][0]["imbalance_ratio"] is None # Missing data should be None
