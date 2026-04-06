"""
GoldTrader AI Agent — Technical Indicators
Calculates all indicators from raw candles: EMA, RSI, MACD, ATR, body ratios.
Reference: PLAYBOOK.md Three Pillars, mt5-bot/src for patterns
"""

import logging
from typing import Optional

logger = logging.getLogger("indicators")


# ------------------------------------------------------------------
# Core Indicator Functions
# ------------------------------------------------------------------

def calculate_ema(candles: list, period: int) -> list:
    """
    Calculate EMA from candle close prices.
    Returns list of EMA values (same length as candles, early values are SMA).
    """
    if not candles or len(candles) < period:
        return []

    closes = [c["close"] for c in candles]
    multiplier = 2.0 / (period + 1)

    # Seed with SMA
    sma = sum(closes[:period]) / period
    ema_values = [None] * (period - 1) + [sma]

    for i in range(period, len(closes)):
        ema = (closes[i] - ema_values[-1]) * multiplier + ema_values[-1]
        ema_values.append(ema)

    return ema_values


def calculate_rsi(candles: list, period: int = 14) -> float:
    """
    Calculate RSI from candle close prices.
    Returns current RSI value (0-100).
    """
    if not candles or len(candles) < period + 1:
        return 50.0  # Neutral default

    closes = [c["close"] for c in candles]
    deltas = [closes[i] - closes[i - 1] for i in range(1, len(closes))]

    gains = []
    losses = []
    for d in deltas[:period]:
        if d > 0:
            gains.append(d)
            losses.append(0.0)
        else:
            gains.append(0.0)
            losses.append(abs(d))

    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period

    # Smooth with Wilder's method
    for d in deltas[period:]:
        if d > 0:
            avg_gain = (avg_gain * (period - 1) + d) / period
            avg_loss = (avg_loss * (period - 1) + 0.0) / period
        else:
            avg_gain = (avg_gain * (period - 1) + 0.0) / period
            avg_loss = (avg_loss * (period - 1) + abs(d)) / period

    if avg_loss == 0:
        return 100.0

    rs = avg_gain / avg_loss
    return round(100.0 - (100.0 / (1.0 + rs)), 2)


def calculate_macd(candles: list) -> dict:
    """
    Calculate MACD (12, 26, 9) from candle close prices.
    Returns: {macd_line, signal_line, histogram, slope}
    Slope: positive = expanding, negative = contracting.
    """
    if not candles or len(candles) < 26:
        return {"macd_line": 0.0, "signal_line": 0.0, "histogram": 0.0, "slope": "flat"}

    ema_12 = calculate_ema(candles, 12)
    ema_26 = calculate_ema(candles, 26)

    # MACD line = EMA12 - EMA26 (only where both exist)
    macd_line_values = []
    for i in range(len(candles)):
        if i < 25 or ema_12[i] is None or ema_26[i] is None:
            continue
        macd_line_values.append(ema_12[i] - ema_26[i])

    if len(macd_line_values) < 9:
        return {"macd_line": 0.0, "signal_line": 0.0, "histogram": 0.0, "slope": "flat"}

    # Signal line = 9-period EMA of MACD line
    multiplier = 2.0 / 10
    signal = sum(macd_line_values[:9]) / 9
    signal_values = [signal]
    for val in macd_line_values[9:]:
        signal = (val - signal) * multiplier + signal
        signal_values.append(signal)

    current_macd = macd_line_values[-1]
    current_signal = signal_values[-1]
    current_histogram = current_macd - current_signal

    # Slope: compare last 3 histogram values
    if len(macd_line_values) >= 3:
        recent_histograms = [
            macd_line_values[-(i + 1)] - signal_values[-(i + 1)]
            for i in range(min(3, len(signal_values)))
        ]
        recent_histograms.reverse()

        if len(recent_histograms) >= 2:
            if abs(recent_histograms[-1]) > abs(recent_histograms[-2]):
                slope = "expanding"
            elif abs(recent_histograms[-1]) < abs(recent_histograms[-2]):
                slope = "contracting"
            else:
                slope = "flat"
        else:
            slope = "flat"
    else:
        slope = "flat"

    return {
        "macd_line": round(current_macd, 4),
        "signal_line": round(current_signal, 4),
        "histogram": round(current_histogram, 4),
        "slope": slope,
    }


def calculate_atr(candles: list, period: int = 14) -> float:
    """
    Calculate Average True Range.
    Returns current ATR value.
    """
    if not candles or len(candles) < period + 1:
        return 0.0

    true_ranges = []
    for i in range(1, len(candles)):
        high = candles[i]["high"]
        low = candles[i]["low"]
        prev_close = candles[i - 1]["close"]

        tr = max(
            high - low,
            abs(high - prev_close),
            abs(low - prev_close),
        )
        true_ranges.append(tr)

    if len(true_ranges) < period:
        return sum(true_ranges) / len(true_ranges) if true_ranges else 0.0

    # Wilder's smoothing
    atr = sum(true_ranges[:period]) / period
    for tr in true_ranges[period:]:
        atr = (atr * (period - 1) + tr) / period

    return round(atr, 4)


def calculate_body_ratio(candle: dict) -> float:
    """
    Body-to-total range ratio as percentage (0-100).
    Body dominates wick = conviction. Wick dominates body = rejection.
    Reference: PLAYBOOK.md Candle Reading Rules
    """
    high = candle["high"]
    low = candle["low"]
    total_range = high - low

    if total_range == 0:
        return 0.0

    body = abs(candle["close"] - candle["open"])
    return round((body / total_range) * 100, 1)


def calculate_strength(candles: list, fast_period: int = 9, slow_period: int = 21) -> float:
    """
    EMA crossover strength score (0-10 scale).
    Based on distance between fast EMA and slow EMA relative to ATR.
    """
    if not candles or len(candles) < slow_period:
        return 0.0

    ema_fast = calculate_ema(candles, fast_period)
    ema_slow = calculate_ema(candles, slow_period)

    if not ema_fast or not ema_slow:
        return 0.0

    fast_val = ema_fast[-1]
    slow_val = ema_slow[-1]

    if fast_val is None or slow_val is None:
        return 0.0

    distance = fast_val - slow_val
    atr = calculate_atr(candles)

    if atr == 0:
        return 0.0

    # Normalize: distance / ATR, capped at 10
    raw_score = abs(distance) / atr
    score = min(10.0, raw_score * 2)  # Scale so 5 ATR distance = 10

    return round(score, 1)


def get_ema_direction(candles: list, fast_period: int = 9, slow_period: int = 21) -> str:
    """Determine trend direction from EMA crossover."""
    if not candles or len(candles) < slow_period:
        return "NEUTRAL"

    ema_fast = calculate_ema(candles, fast_period)
    ema_slow = calculate_ema(candles, slow_period)

    if not ema_fast or not ema_slow or ema_fast[-1] is None or ema_slow[-1] is None:
        return "NEUTRAL"

    if ema_fast[-1] > ema_slow[-1]:
        return "BUY"
    elif ema_fast[-1] < ema_slow[-1]:
        return "SELL"
    return "NEUTRAL"


def get_ema_consecutive_bars(candles: list, fast_period: int = 9, slow_period: int = 21) -> int:
    """
    Count how many consecutive recent candles have held the same EMA direction.
    Returns 0 if direction is NEUTRAL or data is insufficient.
    A value of 1 means the direction just flipped on the last candle.
    """
    if not candles or len(candles) < slow_period + 1:
        return 0

    ema_fast = calculate_ema(candles, fast_period)
    ema_slow = calculate_ema(candles, slow_period)

    if not ema_fast or not ema_slow:
        return 0

    # Build per-bar direction from the point both EMAs are valid
    directions = []
    for f, s in zip(ema_fast, ema_slow):
        if f is None or s is None:
            directions.append("NEUTRAL")
        elif f > s:
            directions.append("BUY")
        elif f < s:
            directions.append("SELL")
        else:
            directions.append("NEUTRAL")

    if not directions:
        return 0

    current = directions[-1]
    if current == "NEUTRAL":
        return 0

    count = 0
    for d in reversed(directions):
        if d == current:
            count += 1
        else:
            break

    return count


# ------------------------------------------------------------------
# Session Levels
# ------------------------------------------------------------------

def get_session_levels(candles_h1: list) -> dict:
    """
    Calculate session high and low from H1 candles.
    Returns: {session_high, session_low, asia_high, asia_low}
    """
    if not candles_h1:
        return {"session_high": 0, "session_low": 0, "asia_high": 0, "asia_low": 0}

    # All candles for session range
    highs = [c["high"] for c in candles_h1]
    lows = [c["low"] for c in candles_h1]

    # Asia range: identify candles between 23:00-08:00 UTC
    asia_highs = []
    asia_lows = []
    for c in candles_h1:
        try:
            from datetime import datetime as dt
            if isinstance(c["time"], str):
                t = dt.fromisoformat(c["time"].replace("Z", "+00:00"))
            else:
                t = c["time"]
            hour = t.hour
            if 23 <= hour or hour < 8:
                asia_highs.append(c["high"])
                asia_lows.append(c["low"])
        except Exception:
            continue

    return {
        "session_high": max(highs) if highs else 0,
        "session_low": min(lows) if lows else 0,
        "asia_high": max(asia_highs) if asia_highs else 0,
        "asia_low": min(asia_lows) if asia_lows else 0,
    }


def get_price_position(price: float, high: float, low: float) -> float:
    """
    Where price sits in the range as percentage (0-100).
    0 = at session low, 100 = at session high, 50 = mid-range.
    Reference: PLAYBOOK.md Pillar 3 Location
    """
    if high == low:
        return 50.0
    position = ((price - low) / (high - low)) * 100
    return round(max(0.0, min(100.0, position)), 1)


def get_m30_sequence(candles_m30: list, count: int = 5) -> list:
    """
    Last N M30 candles summarized for context.
    Returns list of: {direction, body_ratio, close}
    """
    if not candles_m30:
        return []

    recent = candles_m30[-count:]
    sequence = []
    for c in recent:
        direction = "BULL" if c["close"] >= c["open"] else "BEAR"
        sequence.append({
            "direction": direction,
            "body_ratio": calculate_body_ratio(c),
            "close": c["close"],
        })
    return sequence


# ------------------------------------------------------------------
# Timeframe Analysis (combines all indicators for one TF)
# ------------------------------------------------------------------

def analyse_timeframe(candles: list, tf_name: str) -> dict:
    """
    Full indicator suite for one timeframe.
    Returns dict matching PLAYBOOK.md Context Package.
    """
    if not candles:
        return {
            "timeframe": tf_name,
            "direction": "NEUTRAL",
            "consecutive_bars": 0,
            "strength": 0.0,
            "rsi": 50.0,
            "macd": {"macd_line": 0, "signal_line": 0, "histogram": 0, "slope": "flat"},
            "atr": 0.0,
            "body_ratio": 0.0,
        }

    direction = get_ema_direction(candles)
    consecutive_bars = get_ema_consecutive_bars(candles)
    strength = calculate_strength(candles)
    rsi = calculate_rsi(candles)
    macd = calculate_macd(candles)
    atr = calculate_atr(candles)
    body_ratio = calculate_body_ratio(candles[-1]) if candles else 0.0

    return {
        "timeframe": tf_name,
        "direction": direction,
        "consecutive_bars": consecutive_bars,
        "strength": strength,
        "rsi": rsi,
        "macd": macd,
        "atr": atr,
        "body_ratio": body_ratio,
    }
