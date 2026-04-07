import pytest
import json
import gzip
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from collector.metrics.whale_detector import WhaleDetector

@pytest.mark.asyncio
async def test_whale_detection_logic():
    detector = WhaleDetector()
    detector.redis = AsyncMock()
    detector.pg_pool = AsyncMock()

    symbol = "BTC-USDT"
    # Whale size is 50,000 USD.
    # Price 50,000, Size 1.1 -> 55,000 USD (Whale)
    # Price 50,000, Size 0.1 -> 5,000 USD (Not Whale)

    snapshot = {
        "symbol": symbol,
        "ts": 1712516400000, # Some timestamp
        "bids": [[50000.0, 1.1], [49990.0, 0.1]],
        "asks": [[50100.0, 0.5], [50110.0, 1.5]] # 1.5 * 50110 = 75165 (Whale)
    }

    with patch("collector.metrics.whale_detector.datetime") as mock_dt:
        mock_now = datetime(2024, 4, 7, 19, 0, 0, tzinfo=timezone.utc)
        mock_dt.fromtimestamp.return_value = mock_now
        mock_dt.isoformat.return_value = mock_now.isoformat()

        await detector.process_snapshot(snapshot)

        # Should have emitted 2 alerts: 1 bid whale, 1 ask whale
        assert detector.redis.publish.call_count == 2

        # Verify first alert (bid)
        call_args = detector.redis.publish.call_args_list[0]
        assert call_args[0][0] == f"whales:{symbol}"
        alert = json.loads(call_args[0][1])
        assert alert["type"] == "whale_bid"
        assert pytest.approx(alert["size_usd"]) == 55000.0

        # Verify second alert (ask)
        call_args = detector.redis.publish.call_args_list[1]
        alert = json.loads(call_args[0][1])
        assert alert["type"] == "whale_ask"
        assert pytest.approx(alert["size_usd"]) == 50110.0 * 1.5

@pytest.mark.asyncio
async def test_iceberg_detection():
    detector = WhaleDetector()
    detector.redis = AsyncMock()
    detector.pg_pool = AsyncMock()

    symbol = "BTC-USDT"
    price = 50000.0
    size = 2.0 # 100,000 USD

    snapshot = {
        "symbol": symbol,
        "ts": 1712516400000,
        "bids": [[price, size]],
        "asks": [[51000.0, 0.1]]
    }

    # Send 5 identical snapshots
    for i in range(5):
        snapshot["ts"] += 500 # 500ms later
        await detector.process_snapshot(snapshot)

    # Total alerts should be 2:
    # 1. Initial whale_bid (tick 1)
    # 2. Iceberg (tick 5)
    assert detector.redis.publish.call_count == 2

    # Check the second alert is iceberg
    call_args = detector.redis.publish.call_args_list[1]
    alert = json.loads(call_args[0][1])
    assert alert["type"] == "iceberg"
    assert alert["persisted_ticks"] == 5

    # Send 6th snapshot - should NOT emit another iceberg alert
    snapshot["ts"] += 500
    await detector.process_snapshot(snapshot)
    assert detector.redis.publish.call_count == 2
