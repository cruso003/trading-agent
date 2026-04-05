"""
GoldTrader AI Agent — Prefilter
Zero API cost local signal gate. Runs before any paid API call.
Reference: ARCHITECTURE.md Section 3, PLAYBOOK.md Three Pillars
"""

import logging
from datetime import datetime, timezone

logger = logging.getLogger("prefilter")


def run_prefilter(
    indicators: dict,
    window_status: dict,
    market_positions: list,
    db,
    config,
) -> tuple:
    """
    Zero-cost local prefilter. Checks in order per ARCHITECTURE.md:
    1. H4 and H1 direction agree
    2. M30 body strength not in dead zone (40-55%)
    3. Not in post-trade cooling period (20min normal, 30min after loss)
    4. Price not mid-range (position 35-65%)
    5. No position already open in same direction

    Args:
        indicators: dict with keys "H4", "H1", "M30", "M15", "session_levels", "current_price"
        window_status: dict with "window" and "minutes_into_window"
        market_positions: list of open positions from market.get_open_positions()
        db: Database instance
        config: Config instance

    Returns:
        (passed: bool, reason: str)
        reason is empty string if passed, specific failure reason if not.
    """

    # ---------------------------------------------------------------
    # Check 1: H4 and H1 direction agree
    # ---------------------------------------------------------------
    h4 = indicators.get("H4", {})
    h1 = indicators.get("H1", {})
    h4_dir = h4.get("direction", "NEUTRAL")
    h1_dir = h1.get("direction", "NEUTRAL")

    if h4_dir != "NEUTRAL" and h1_dir != "NEUTRAL" and h4_dir != h1_dir:
        reason = f"htf_conflict: H4={h4_dir}, H1={h1_dir}"
        logger.info(f"FAIL | {reason}")
        return (False, reason)

    # ---------------------------------------------------------------
    # Check 2: M30 body strength not in dead zone (40-55%)
    # ---------------------------------------------------------------
    m30 = indicators.get("M30", {})
    m30_body = m30.get("body_ratio", 50.0)

    if 40.0 <= m30_body <= 55.0:
        reason = f"dead_zone: M30 body_ratio={m30_body}%"
        logger.info(f"FAIL | {reason}")
        return (False, reason)

    # ---------------------------------------------------------------
    # Check 3: Not in post-trade cooling period
    # ---------------------------------------------------------------
    last_trade_time = db.get_last_trade_time()
    if last_trade_time:
        try:
            last_dt = datetime.fromisoformat(last_trade_time)
            if last_dt.tzinfo is None:
                last_dt = last_dt.replace(tzinfo=timezone.utc)

            now = datetime.now(timezone.utc)
            elapsed_minutes = (now - last_dt).total_seconds() / 60

            # Check if last trade was a loss (longer cooling)
            was_loss = db.get_last_trade_was_loss()
            cooling = config.post_loss_cooling_minutes if was_loss else config.post_trade_cooling_minutes

            if elapsed_minutes < cooling:
                remaining = int(cooling - elapsed_minutes)
                reason = f"cooling_period: {remaining}min remaining ({'loss' if was_loss else 'normal'})"
                logger.info(f"FAIL | {reason}")
                return (False, reason)
        except Exception as e:
            logger.warning(f"Cooling period check error: {e}")

    # ---------------------------------------------------------------
    # Check 4: Price not mid-range (position 35-65%)
    # ---------------------------------------------------------------
    session = indicators.get("session_levels", {})
    current_price = indicators.get("current_price", 0)
    session_high = session.get("session_high", 0)
    session_low = session.get("session_low", 0)

    if session_high > session_low and current_price > 0:
        position_pct = ((current_price - session_low) / (session_high - session_low)) * 100

        if 35.0 <= position_pct <= 65.0:
            reason = f"mid_range: position_pct={position_pct:.1f}%"
            logger.info(f"FAIL | {reason}")
            return (False, reason)

    # ---------------------------------------------------------------
    # Check 5: No position already open in same direction
    # ---------------------------------------------------------------
    # Determine intended direction from H1 bias
    intended_direction = h1_dir if h1_dir != "NEUTRAL" else h4_dir

    if intended_direction != "NEUTRAL" and market_positions:
        for pos in market_positions:
            if pos.get("direction") == intended_direction:
                reason = f"duplicate_direction: already {intended_direction} open (ticket {pos.get('ticket', '?')})"
                logger.info(f"FAIL | {reason}")
                return (False, reason)

    # ---------------------------------------------------------------
    # All checks passed
    # ---------------------------------------------------------------
    logger.info(
        f"PASS | H4={h4_dir}, H1={h1_dir}, M30_body={m30_body}%, "
        f"price_pos={position_pct:.1f}% (if calculated)"
        if session_high > session_low and current_price > 0
        else f"PASS | H4={h4_dir}, H1={h1_dir}, M30_body={m30_body}%"
    )
    return (True, "")
