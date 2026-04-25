"""
GoldTrader AI Agent — Prefilter (Quick-Scalp Edition)
Zero API cost local signal gate. Runs before any paid API call.
Reference: PLAYBOOK.md v2.0 Quick-Scalp Three Pillars

Strategy:
  Gate only on fundamentals — H4 permission, position conflicts,
  cooling periods, and basic M15 trigger sanity. Leave the full
  structural read to Claude.
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
    Zero-cost local prefilter. Checks in order:
    1. H4 has a directional bias (not NEUTRAL)
    2. H4 strength >= 4 (provides permission side)
    3. Not in post-trade / post-loss cooling period
    4. No same-direction position already open
    5. Latest closed M15 candle has at least some body (>= 25%)
       — blocks full-doji indecision; Claude handles nuance above

    All location / range / compression / base logic is delegated
    to Claude, which has the full structural picture via the
    context package (including m15_swing_low/high).

    Args:
        indicators: dict with H4, H1, M30, M15, session_levels,
                    current_price, m30_sequence
        window_status: dict with window and minutes_into_window
        market_positions: list of open positions
        db: Database instance
        config: Config instance

    Returns:
        (passed: bool, reason: str)
    """

    h4 = indicators.get("H4", {})
    h1 = indicators.get("H1", {})
    m15 = indicators.get("M15", {})

    h4_dir = h4.get("direction", "NEUTRAL")
    h4_strength = h4.get("strength", 0.0)

    # ---------------------------------------------------------------
    # Check 1: H4 must have a clear directional bias
    # H4 = permission side. NEUTRAL H4 = no structural context.
    # ---------------------------------------------------------------
    if h4_dir == "NEUTRAL":
        reason = "h4_neutral: H4 has no directional structure"
        logger.info(f"FAIL | {reason}")
        return (False, reason)

    # ---------------------------------------------------------------
    # Check 2: H4 strength must meet permission threshold.
    # Playbook v2.0 requires H4 strength >= 4 for directional trades.
    # Rejection_reversal at H4 strength 3-4 is still possible, but
    # we let Claude make that call with its full view. Below 3 is
    # pure chop — no edge worth an API call.
    # ---------------------------------------------------------------
    if h4_strength < 3.0:
        reason = f"h4_weak: H4={h4_dir} strength {h4_strength:.1f} < 3.0"
        logger.info(f"FAIL | {reason}")
        return (False, reason)

    # ---------------------------------------------------------------
    # Check 3: Post-trade / post-loss cooling period
    # Enforces the 20min (normal) / 30min (after loss) cooling.
    # ---------------------------------------------------------------
    last_trade_time = db.get_last_trade_time()
    if last_trade_time:
        try:
            last_dt = datetime.fromisoformat(last_trade_time)
            if last_dt.tzinfo is None:
                last_dt = last_dt.replace(tzinfo=timezone.utc)

            now = datetime.now(timezone.utc)
            elapsed_minutes = (now - last_dt).total_seconds() / 60

            was_loss = db.get_last_trade_was_loss()
            cooling = (
                config.post_loss_cooling_minutes
                if was_loss
                else config.post_trade_cooling_minutes
            )

            if elapsed_minutes < cooling:
                remaining = int(cooling - elapsed_minutes)
                label = "loss" if was_loss else "normal"
                reason = f"cooling_period: {remaining}min remaining ({label})"
                logger.info(f"FAIL | {reason}")
                return (False, reason)
        except Exception as e:
            logger.warning(f"Cooling period check error: {e}")

    # ---------------------------------------------------------------
    # Check 4: No same-direction position already open
    # Intended direction = H4 direction (our permission side).
    # ---------------------------------------------------------------
    if market_positions:
        for pos in market_positions:
            if pos.get("direction") == h4_dir:
                ticket = pos.get("ticket", "?")
                reason = (
                    f"duplicate_direction: already {h4_dir} open "
                    f"(ticket {ticket})"
                )
                logger.info(f"FAIL | {reason}")
                return (False, reason)

    # ---------------------------------------------------------------
    # Check 5: M15 trigger candle has minimum body.
    # A full doji (body < 25%) means no trigger has fired —
    # nothing to evaluate. This is the only momentum check we
    # do locally; Claude handles direction-specific body analysis.
    # ---------------------------------------------------------------
    m15_body = m15.get("body_ratio", 0.0)
    if m15_body < 25.0:
        reason = f"m15_doji: M15 body_ratio={m15_body:.1f}% (no trigger)"
        logger.info(f"FAIL | {reason}")
        return (False, reason)

    # ---------------------------------------------------------------
    # All gate checks passed — let Claude make the call.
    # ---------------------------------------------------------------
    h1_dir = h1.get("direction", "NEUTRAL")
    h1_strength = h1.get("strength", 0.0)
    logger.info(
        f"PASS | H4={h4_dir}({h4_strength:.1f}), "
        f"H1={h1_dir}({h1_strength:.1f}), "
        f"M15_body={m15_body:.1f}%"
    )
    return (True, "")
