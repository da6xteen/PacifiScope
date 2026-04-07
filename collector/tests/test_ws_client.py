import pytest
import json
import gzip
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from ws_client import OrderbookCollector

@pytest.fixture
def collector():
    with patch("ws_client.Redis"), patch("ws_client.Counter"):
        collector = OrderbookCollector()
        collector.symbols = ["BTC"]
        collector.orderbooks["BTC"] = {
            "bids": collector.orderbooks.get("BTC", {}).get("bids", MagicMock()),
            "asks": collector.orderbooks.get("BTC", {}).get("asks", MagicMock())
        }
        # Use actual SortedDict for the test
        from sortedcontainers import SortedDict
        collector.orderbooks["BTC"] = {
            "bids": SortedDict(),
            "asks": SortedDict()
        }
        return collector

def test_process_l2_update(collector):
    # Initial snapshot
    data = {
        "s": "BTC",
        "l": [
            [{"p": "50000", "a": "1.5"}, {"p": "49990", "a": "2.0"}], # Bids
            [{"p": "50010", "a": "1.0"}, {"p": "50020", "a": "0.5"}]  # Asks
        ]
    }
    collector.process_l2_update(data)

    assert collector.orderbooks["BTC"]["bids"][50000.0] == 1.5
    assert collector.orderbooks["BTC"]["bids"][49990.0] == 2.0
    assert collector.orderbooks["BTC"]["asks"][50010.0] == 1.0
    assert collector.orderbooks["BTC"]["asks"][50020.0] == 0.5

    # Delta update: upsert and remove
    delta = {
        "s": "BTC",
        "l": [
            [{"p": "50000", "a": "2.5"}, {"p": "49990", "a": "0"}], # Bids: update 50000, remove 49990
            [{"p": "50010", "a": "0"}, {"p": "50030", "a": "1.2"}]  # Asks: remove 50010, add 50030
        ]
    }
    collector.process_l2_update(delta)

    assert collector.orderbooks["BTC"]["bids"][50000.0] == 2.5
    assert 49990.0 not in collector.orderbooks["BTC"]["bids"]
    assert 50010.0 not in collector.orderbooks["BTC"]["asks"]
    assert collector.orderbooks["BTC"]["asks"][50030.0] == 1.2

@pytest.mark.asyncio
async def test_publish_snapshots(collector):
    # Setup some data
    collector.orderbooks["BTC"]["bids"][50000.0] = 1.0
    collector.orderbooks["BTC"]["asks"][50010.0] = 1.0

    collector.redis = MagicMock()

    # Run publish_snapshots once (we'll break the loop)
    collector.running = True

    # We can't easily run the infinite loop, so we'll mock it or just call the logic
    # Let's mock time.sleep to raise an exception to break the loop
    with patch("asyncio.sleep", side_effect=asyncio.CancelledError):
        try:
            await collector.publish_snapshots()
        except asyncio.CancelledError:
            pass

    # Verify redis publish was called
    assert collector.redis.publish.called
    args, kwargs = collector.redis.publish.call_args
    channel = args[0]
    compressed_payload = args[1]

    assert channel == "orderbook:BTC"
    payload = json.loads(gzip.decompress(compressed_payload).decode("utf-8"))
    assert payload["symbol"] == "BTC"
    assert payload["bids"] == [[50000.0, 1.0]]
    assert payload["asks"] == [[50010.0, 1.0]]

@pytest.mark.asyncio
async def test_fetch_symbols(collector):
    mock_data = {
        "success": True,
        "data": [{"symbol": "BTC"}, {"symbol": "ETH"}]
    }

    # Mock aiohttp
    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json.return_value = mock_data
        mock_get.return_value.__aenter__.return_value = mock_resp

        await collector.fetch_symbols()

    assert "BTC" in collector.symbols
    assert "ETH" in collector.symbols
    assert "BTC" in collector.orderbooks
    assert "ETH" in collector.orderbooks
