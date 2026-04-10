"""
GoldTrader AI Agent — Prefilter
Zero API cost local signal gate. Runs before any paid API call.
Reference: ARCHITECTURE.md Section 3, PLAYBOOK.md Three Pillars

Strategy: H4 is the permission side (allowed direction only).
The ideal entry is a pullback WITHIN the H4 trend, not momentum
continuation after all timeframes have already agreed.
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
    1. H4 has a clear directional bias (not NEUTRAL)
    2. H4 direction is confirmed (held >= 2 bars, not a fresh flip)
    3. M30 sequence not showing unrecovered counter-trend momentum
    4. M30 body not in dead zone (40-55%)
    5. Price not extended (4+/5 recent M30 bars in H4 direction)
    6. Not in post-trade cooling period
    7. Price not mid-range (position 35-65%)
    8. No position already open in same direction

    Args:
        indicators: dict with keys "H4", "H1", "M30", "M15",
                    "session_levels", "current_price", "m30_sequence"
        window_status: dict with "window" and "minutes_into_window"
        market_positions: list of open positions
        db: Database instance
        config: Config instance

    Returns:
        (passed: bool, reason: str)
    """

    h4 = indicators.get("H4", {})
    h1 = indicators.get("H1", {})
    m30 = indicators.get("M30", {})
    h4_dir = h4.get("direction", "NEUTRAL")
    h1_dir = h1.get("direction", "NEUTRAL")

    # ---------------------------------------------------------------
    # Check 1: H4 must have a clear directional bias
    # H4 = permission side only. NEUTRAL H4 = no structural context,
    # no trade. We are not in the business of picking direction from
    # scratch — we trade WITH established structure.
    # ---------------------------------------------------------------
    if h4_dir == "NEUTRAL":
        reason = "no_bias: H4 has no directional structure"
        logger.info(f"FAIL | {reason}")
        return (False, reason)

    # ---------------------------------------------------------------
    # Check 2: H4 must have held its direction for at least 2 bars
    # Prevents trading a fresh H4 flip before it's confirmed.
    # A 1-bar H4 flip could be a single large candle anomaly.
    # ---------------------------------------------------------------
    h4_consecutive = h4.get("consecutive_bars", 0)
    if h4_consecutive < 2:
        reason = f"htf_fresh_flip: H4={h4_dir} only {h4_consecutive} bar(s) old"
        logger.info(f"FAIL | {reason}")
        return (False, reason)

    # ---------------------------------------------------------------
    # Check 3: M30 sequence must not show strong unrecovered
    # counter-H4 momentum.
    #
    # Key distinction:
    # - 2+ strong counter-H4 M30 bars WITH the latest bar recovering
    #   back to H4 direction = pullback completing → PASS (this is
    #   exactly the setup we want to catch)
    # - 2+ strong counter-H4 M30 bars AND the latest bar is STILL
    #   counter-H4 = momentum reversal in progress → FAIL
    # ---------------------------------------------------------------
    STRONG_BODY = 60.0
    m30_sequence = indicators.get("m30_sequence", [])

    if len(m30_sequence) >= 3:
        last_three = m30_sequence[-3:]
        strong_conflicts = sum(
            1 for c in last_three
            if ("BUY" if c.get("direction") == "BULL" else "SELL") != h4_dir
            and c.get("body_ratio", 0) > STRONG_BODY
        )

        # Latest bar recovering back into H4 direction?
        latest_bar_dir = "BUY" if last_three[-1].get("direction") == "BULL" else "SELL"
        recovering = (latest_bar_dir == h4_dir)

        if strong_conflicts >= 2 and not recovering:
            reason = (
                f"m30_momentum_reversal: {strong_conflicts} strong counter-H4 M30 bars "
                f"with no recovery — potential trend change, not a pullback"
            )
            logger.info(f"FAIL | {reason}")
            return (False, reason)

    # ---------------------------------------------------------------
    # Check 4: M30 body not in dead zone (40-55%)
    # Neither conviction nor pullback — indecisive chop.
    # ---------------------------------------------------------------
    m30_body = m30.get("body_ratio", 50.0)

    if 40.0 <= m30_body <= 55.0:
        reason = f"dead_zone: M30 body_ratio={m30_body}%"
        logger.info(f"FAIL | {reason}")
        return (False, reason)

    # ---------------------------------------------------------------
    # Check 5: Price not in an extended one-directional run
    # If 4+ of the last 5 M30 candles are in H4 direction with
    # conviction bodies, the move is mature — we are chasing.
    # The right time to enter was 5 bars ago, not now.
    # ---------------------------------------------------------------
    if len(m30_sequence) >= 5:
        extended_bars = sum(
            1 for c in m30_sequence[-5:]
            if ("BUY" if c.get("direction") == "BULL" else "SELL") == h4_dir
            and c.get("body_ratio", 0) > 50
        )
        if extended_bars >= 4:
            reason = (
                f"extended_move: {extended_bars}/5 recent M30 bars in H4 direction "
                f"— move is mature, waiting for pullback"
            )
            logger.info(f"FAIL | {reason}")
            return (False, reason)

    # ---------------------------------------------------------------
    # Check 6: Not in post-trade cooling period
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
            cooling = config.post_loss_cooling_minutes if was_loss else config.post_trade_cooling_minutes

            if elapsed_minutes < cooling:
                remaining = int(cooling - elapsed_minutes)
                reason = f"cooling_period: {remaining}min remaining ({'loss' if was_loss else 'normal'})"
                logger.info(f"FAIL | {reason}")
                return (False, reason)
        except Exception as e:
            logger.warning(f"Cooling period check error: {e}")

    # ---------------------------------------------------------------
    # Check 7: Price not mid-range (position 35-65%)
    # Mid-range = no edge. Price at the edge of range has a defined
    # direction to push. Price in the middle can go either way.
    # ---------------------------------------------------------------
    session = indicators.get("session_levels", {})
    current_price = indicators.get("current_price", 0)
    session_high = session.get("session_high", 0)
    session_low = session.get("session_low", 0)
    position_pct = None

    if session_high > session_low and current_price > 0:
        position_pct = ((current_price - session_low) / (session_high - session_low)) * 100

        if 35.0 <= position_pct <= 65.0:
            reason = f"mid_range: position_pct={position_pct:.1f}%"
            logger.info(f"FAIL | {reason}")
            return (False, reason)

    # ---------------------------------------------------------------
    # Check 8: No position already open in same direction
    # ---------------------------------------------------------------
    intended_direction = h1_dir if h1_dir != "NEUTRAL" else h4_dir

    if intended_direction != "NEUTRAL" and market_positions:
        for pos in market_positions:
            if pos.get("direction") == intended_direction:
                reason = (
                    f"duplicate_direction: already {intended_direction} open "
                    f"(ticket {pos.get('ticket', '?')})"
                )
                logger.info(f"FAIL | {reason}")
                return (False, reason)

    # ---------------------------------------------------------------
    # All checks passed
    # ---------------------------------------------------------------
    if position_pct is not None:
        logger.info(
            f"PASS | H4={h4_dir}({h4_consecutive}bars), H1={h1_dir}, "
            f"M30_body={m30_body}%, price_pos={position_pct:.1f}%"
        )
    else:
        logger.info(
            f"PASS | H4={h4_dir}({h4_consecutive}bars), H1={h1_dir}, "
            f"M30_body={m30_body}%"
        )
    return (True, "")
