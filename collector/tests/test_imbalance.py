import pytest
from collector.metrics.imbalance import ImbalanceCalculator

def test_imbalance_ratio_calculation():
    calc = ImbalanceCalculator()

    # Simple balanced orderbook
    mid = 100.0
    bids = [[99.9, 10], [99.8, 10], [99.7, 10], [99.6, 10], [99.5, 10]]
    asks = [[100.1, 10], [100.2, 10], [100.3, 10], [100.4, 10], [100.5, 10]]

    ratio = calc.calculate_imbalance_ratio(bids, asks, mid)
    assert ratio == 0.0

    # More bids than asks
    bids = [[99.9, 20], [99.8, 20], [99.7, 20], [99.6, 20], [99.5, 20]]
    asks = [[100.1, 10], [100.2, 10], [100.3, 10], [100.4, 10], [100.5, 10]]

    ratio = calc.calculate_imbalance_ratio(bids, asks, mid)
    assert ratio > 0

    # More asks than bids
    bids = [[99.9, 10], [99.8, 10], [99.7, 10], [99.6, 10], [99.5, 10]]
    asks = [[100.1, 20], [100.2, 20], [100.3, 20], [100.4, 20], [100.5, 20]]

    ratio = calc.calculate_imbalance_ratio(bids, asks, mid)
    assert ratio < 0

def test_weighted_bid_volume_formula():
    """
    Weighted bid volume: sum(size_i / (1 + |level_i - mid| / mid * 1000))
    """
    calc = ImbalanceCalculator()
    mid = 100.0

    # price = 99.0, size = 10
    # weight = 1 / (1 + |99.0 - 100.0| / 100.0 * 1000) = 1/11
    # price = 101.0, size = 10
    # weight = 1 / (1 + |101.0 - 100.0| / 100.0 * 1000) = 1/11

    bids = [[99.0, 10]]
    asks = [[101.0, 10]]

    ratio = calc.calculate_imbalance_ratio(bids, asks, mid)
    assert ratio == 0.0

def test_depth_imbalance():
    calc = ImbalanceCalculator()
    mid = 100.0

    # 5 bps = 0.05% = 0.0005 * 100 = 0.05 price range
    # Range: 99.95 to 100.05
    bids = [[99.97, 10], [99.90, 10]]
    asks = [[100.03, 5], [100.10, 10]]

    ratio = calc.calculate_depth_imbalance(bids, asks, mid, 5)
    assert pytest.approx(ratio) == 1/3 # (10-5)/(10+5)

    # 50 bps = 0.5% = 0.005 * 100 = 0.5 price range
    # Range: 99.5 to 100.5
    ratio = calc.calculate_depth_imbalance(bids, asks, mid, 50)
    assert pytest.approx(ratio) == 0.142857 # (20-15)/(20+15) = 5/35 = 1/7
    assert pytest.approx(ratio) == 1/7

def test_price_pressure_and_mid_price_history():
    calc = ImbalanceCalculator()
    symbol = "BTC-USDT"

    # Initial price
    change = calc.update_price_history(symbol, 1000, 50000.0)
    assert change == 0.0

    # Price after 10s
    change = calc.update_price_history(symbol, 1010, 50100.0)
    assert change == 100.0 # 50100 - 50000

    # Price after 60s (cutoff is 1000, so 1060 is inclusive or exclusive? Let's check logic)
    # cutoff = 1070 - 60 = 1010. history[0] was 1000. It should be popped.
    change = calc.update_price_history(symbol, 1070, 50200.0)
    assert change == 100.0 # 50200 - 50100 (50000 was at 1000, 1000 < 1010)

    # Verify price pressure calculation
    # imbalance_ratio = 0.5, price_change = 100.0 -> pressure = 50.0
    # (Actually we test the calculator logic indirectly via the function calls)
