"""
GoldTrader AI Agent — Trading Window Detection
Detects active trading windows from GMT+0 time.
Reference: ARCHITECTURE.md Section 8
"""

from datetime import datetime, timezone, timedelta
from typing import Optional


# Window definitions (GMT+0)
# Window 1 crosses midnight: 23:00 - 01:00
# Window 2 is intraday: 12:00 - 14:00
WINDOW_1_NAME = "WINDOW_1"
WINDOW_2_NAME = "WINDOW_2"


def _now_utc() -> datetime:
    """Current UTC time. Isolated for testability."""
    return datetime.now(timezone.utc)


def _parse_time(time_str: str) -> tuple:
    """Parse 'HH:MM' to (hour, minute)."""
    parts = time_str.split(":")
    return int(parts[0]), int(parts[1])


def get_current_window(
    w1_start: str = "23:00",
    w1_end: str = "01:00",
    w2_start: str = "12:00",
    w2_end: str = "14:00",
) -> Optional[str]:
    """
    Return the active window name or None if outside all windows.
    Handles midnight crossover for Window 1 correctly.
    """
    now = _now_utc()
    current_hour = now.hour
    current_minute = now.minute
    current_minutes = current_hour * 60 + current_minute

    # Window 1: crosses midnight (e.g., 23:00 - 01:00)
    w1_start_h, w1_start_m = _parse_time(w1_start)
    w1_end_h, w1_end_m = _parse_time(w1_end)
    w1_start_min = w1_start_h * 60 + w1_start_m
    w1_end_min = w1_end_h * 60 + w1_end_m

    if w1_start_min > w1_end_min:
        # Crosses midnight
        if current_minutes >= w1_start_min or current_minutes < w1_end_min:
            return WINDOW_1_NAME
    else:
        if w1_start_min <= current_minutes < w1_end_min:
            return WINDOW_1_NAME

    # Window 2: same day (e.g., 12:00 - 14:00)
    w2_start_h, w2_start_m = _parse_time(w2_start)
    w2_end_h, w2_end_m = _parse_time(w2_end)
    w2_start_min = w2_start_h * 60 + w2_start_m
    w2_end_min = w2_end_h * 60 + w2_end_m

    if w2_start_min <= current_minutes < w2_end_min:
        return WINDOW_2_NAME

    return None


def is_tradeable_time(
    w1_start: str = "23:00",
    w1_end: str = "01:00",
    w2_start: str = "12:00",
    w2_end: str = "14:00",
) -> bool:
    """True if currently inside any trading window."""
    return get_current_window(w1_start, w1_end, w2_start, w2_end) is not None


def minutes_into_window(
    w1_start: str = "23:00",
    w1_end: str = "01:00",
    w2_start: str = "12:00",
    w2_end: str = "14:00",
) -> int:
    """
    Minutes elapsed since the start of the current window.
    Returns 0 if outside all windows.
    """
    window = get_current_window(w1_start, w1_end, w2_start, w2_end)
    if window is None:
        return 0

    now = _now_utc()
    current_minutes = now.hour * 60 + now.minute

    if window == WINDOW_1_NAME:
        w_start_h, w_start_m = _parse_time(w1_start)
        w_start_min = w_start_h * 60 + w_start_m
        if current_minutes >= w_start_min:
            return current_minutes - w_start_min
        else:
            # After midnight
            return (1440 - w_start_min) + current_minutes
    else:
        w_start_h, w_start_m = _parse_time(w2_start)
        w_start_min = w_start_h * 60 + w_start_m
        return current_minutes - w_start_min


def time_to_next_window(
    w1_start: str = "23:00",
    w1_end: str = "01:00",
    w2_start: str = "12:00",
    w2_end: str = "14:00",
) -> dict:
    """
    Returns {window: str, minutes: int, time: str} for the next window.
    If currently inside a window, returns that window with minutes=0.
    """
    current = get_current_window(w1_start, w1_end, w2_start, w2_end)
    if current is not None:
        return {"window": current, "minutes": 0, "time": "now"}

    now = _now_utc()
    current_minutes = now.hour * 60 + now.minute

    w1_start_h, w1_start_m = _parse_time(w1_start)
    w2_start_h, w2_start_m = _parse_time(w2_start)
    w1_start_min = w1_start_h * 60 + w1_start_m
    w2_start_min = w2_start_h * 60 + w2_start_m

    # Calculate minutes to each window
    mins_to_w1 = (w1_start_min - current_minutes) % 1440
    mins_to_w2 = (w2_start_min - current_minutes) % 1440

    if mins_to_w1 <= mins_to_w2:
        next_time = now + timedelta(minutes=mins_to_w1)
        return {
            "window": WINDOW_1_NAME,
            "minutes": mins_to_w1,
            "time": next_time.strftime("%H:%M"),
        }
    else:
        next_time = now + timedelta(minutes=mins_to_w2)
        return {
            "window": WINDOW_2_NAME,
            "minutes": mins_to_w2,
            "time": next_time.strftime("%H:%M"),
        }


def get_window_name(window_id: Optional[str]) -> str:
    """Human-readable window name."""
    names = {
        WINDOW_1_NAME: "Asia Open (23:00-01:00)",
        WINDOW_2_NAME: "London-NY Overlap (12:00-14:00)",
    }
    return names.get(window_id, "Outside Windows")


def get_current_session() -> str:
    """
    Identify current market session based on GMT+0 time.
    Reference: PLAYBOOK.md Session Behavior Awareness
    """
    now = _now_utc()
    hour = now.hour

    if 23 <= hour or hour < 8:
        return "ASIA"
    elif 8 <= hour < 12:
        return "LONDON"
    elif 12 <= hour < 16:
        return "LONDON_NY_OVERLAP"
    elif 16 <= hour < 21:
        return "NEW_YORK"
    else:
        return "LATE_NY"
