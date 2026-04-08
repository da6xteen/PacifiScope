import pytest
from signals.rules import rule_1_imbalance_level, rule_2_imbalance_trend, rule_3_whale_influence
from signals.signal_engine import SignalEngine
from unittest.mock import MagicMock, AsyncMock
import datetime

def test_rule_1_long():
    readings = [0.4, 0.35, 0.31]
    assert rule_1_imbalance_level(readings) == "LONG"

def test_rule_1_short():
    readings = [-0.4, -0.35, -0.31]
    assert rule_1_imbalance_level(readings) == "SHORT"

def test_rule_1_none():
    readings = [0.4, 0.2, 0.4]
    assert rule_1_imbalance_level(readings) is None

def test_rule_2_long():
    # Linear trend: 0.1, 0.2, 0.3, 0.4, 0.5 -> slope is 0.1
    readings = [0.1, 0.2, 0.3, 0.4, 0.5]
    assert rule_2_imbalance_trend(readings) == "LONG"

def test_rule_2_short():
    readings = [-0.1, -0.2, -0.3, -0.4, -0.5]
    assert rule_2_imbalance_trend(readings) == "SHORT"

def test_rule_3_long():
    readings = [0.1]
    whales = [{"type": "whale_bid"}]
    assert rule_3_whale_influence(readings, whales) == "LONG"

def test_rule_3_short():
    readings = [-0.1]
    whales = [{"type": "whale_ask"}]
    assert rule_3_whale_influence(readings, whales) == "SHORT"

def test_signal_engine_evaluation():
    engine = SignalEngine()
    # Mock data to fire all rules for LONG
    # Rule 2 needs slope > 0.05. 0.1, 0.2, 0.3, 0.4, 0.5 has slope 0.1
    imbalance_readings = [0.1, 0.2, 0.31, 0.41, 0.51] # Rule 1 (last 3 > 0.3) and Rule 2 (slope 0.1)
    recent_whales = [{"type": "whale_bid"}] # Rule 3

    signals = engine.evaluate_signals("BTC/USDT", imbalance_readings, recent_whales)

    print(f"Rules fired: {signals[0]['rules_fired']}")
    assert len(signals) == 1
    assert signals[0]['direction'] == "LONG"
    assert signals[0]['confidence'] == 100.0
    assert set(signals[0]['rules_fired']) == {"RULE_1", "RULE_2", "RULE_3"}
