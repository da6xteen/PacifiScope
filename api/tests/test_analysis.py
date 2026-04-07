import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock

def test_get_correlation(client):
    mock_db = client.app.state.db
    mock_redis = client.app.state.redis
    mock_redis.get.return_value = None

    # Mock some data for correlation
    mock_db.fetch.return_value = [
        {"imbalance_t0": 0.5, "price_change_bps": 10.0},
        {"imbalance_t0": -0.5, "price_change_bps": -10.0},
        {"imbalance_t0": 0.1, "price_change_bps": 2.0},
    ]

    response = client.get("/api/analysis/correlation/BTC-USD")
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "BTC-USD"
    assert "correlation" in data
    assert "r_squared" in data
    assert data["sample_size"] == 3
    assert len(data["data"]) == 3

def test_get_heatmap(client):
    mock_db = client.app.state.db
    mock_redis = client.app.state.redis
    mock_redis.get.return_value = None

    mock_db.fetch.return_value = [
        {"dow": 1, "hour": 10, "date": datetime(2023, 1, 1), "avg_imbalance": 0.2},
        {"dow": 1, "hour": 11, "date": datetime(2023, 1, 1), "avg_imbalance": -0.1},
    ]

    response = client.get("/api/analysis/heatmap/BTC-USD")
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "BTC-USD"
    assert len(data["grid"]) == 2
    assert data["grid"][0]["hour"] == 10
    assert data["grid"][0]["value"] == 0.2
