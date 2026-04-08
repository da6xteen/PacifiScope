from typing import List, Dict, Any, Optional
import numpy as np

def rule_1_imbalance_level(imbalance_readings: List[float]) -> Optional[str]:
    """
    RULE_1: imbalance > 0.3 for 3+ consecutive ticks → LONG signal
    Inverse: imbalance < -0.3 for 3+ consecutive ticks → SHORT signal
    """
    if len(imbalance_readings) < 3:
        return None

    last_3 = imbalance_readings[-3:]

    if all(x > 0.3 for x in last_3):
        return "LONG"
    if all(x < -0.3 for x in last_3):
        return "SHORT"

    return None

def rule_2_imbalance_trend(imbalance_readings: List[float]) -> Optional[str]:
    """
    RULE_2: imbalance_trend (slope) > 0.05/tick for 5 ticks → LONG signal
    Inverse: imbalance_trend (slope) < -0.05/tick for 5 ticks → SHORT signal
    """
    if len(imbalance_readings) < 5:
        return None

    last_5 = imbalance_readings[-5:]
    x = np.arange(5)
    y = np.array(last_5)

    # Calculate slope using linear regression
    slope, _ = np.polyfit(x, y, 1)

    if slope > 0.05:
        return "LONG"
    if slope < -0.05:
        return "SHORT"

    return None

def rule_3_whale_influence(imbalance_readings: List[float], recent_whales: List[Dict[str, Any]]) -> Optional[str]:
    """
    RULE_3: whale_bid event in last 2 min + positive imbalance → LONG signal
    Inverse: whale_ask event in last 2 min + negative imbalance → SHORT signal
    """
    if not imbalance_readings:
        return None

    current_imbalance = imbalance_readings[-1]

    has_whale_bid = any(w['type'] == 'whale_bid' for w in recent_whales)
    has_whale_ask = any(w['type'] == 'whale_ask' for w in recent_whales)

    if has_whale_bid and current_imbalance > 0:
        return "LONG"
    if has_whale_ask and current_imbalance < 0:
        return "SHORT"

    return None
