"""
GoldTrader AI Agent — Risk Management
Pre-execution risk validation and lot size calculation.
Reference: ARCHITECTURE.md Section 8, Section 12
"""

import logging

logger = logging.getLogger("risk")


def validate(
    direction: str,
    entry_price: float,
    sl_level: float,
    db,
    account_info: dict,
    market_positions: list,
    config,
) -> tuple:
    """
    Pre-execution risk validation gauntlet.
    All checks must pass before trade placement.

    Returns: (passed: bool, reason: str)
    """

    # ---------------------------------------------------------------
    # Check 1: Daily loss limit not exceeded
    # ---------------------------------------------------------------
    daily_pnl = db.get_daily_pnl()
    if daily_pnl <= -config.max_daily_loss_usd:
        reason = f"daily_limit: P&L {daily_pnl:.2f} exceeds limit -{config.max_daily_loss_usd}"
        logger.warning(reason)
        return (False, reason)

    # ---------------------------------------------------------------
    # Check 2: Max positions not reached
    # ---------------------------------------------------------------
    open_count = len(market_positions)
    if open_count >= config.max_positions:
        reason = f"max_positions: {open_count} open (max {config.max_positions})"
        logger.warning(reason)
        return (False, reason)

    # ---------------------------------------------------------------
    # Check 3: SL distance between 8-50 points
    # 1 point = $0.01 on XAUUSD (ARCHITECTURE.md Section 12)
    # ---------------------------------------------------------------
    sl_points = get_sl_points(entry_price, sl_level)

    if sl_points < config.sl_min_points:
        reason = f"sl_too_tight: {sl_points:.0f} points (min {config.sl_min_points})"
        logger.warning(reason)
        return (False, reason)

    if sl_points > config.sl_max_points:
        reason = f"sl_too_wide: {sl_points:.0f} points (max {config.sl_max_points})"
        logger.warning(reason)
        return (False, reason)

    # ---------------------------------------------------------------
    # Check 4: Account balance above minimum (can afford the trade)
    # ---------------------------------------------------------------
    balance = account_info.get("balance", 0)
    if balance <= 0:
        reason = f"no_balance: account balance {balance}"
        logger.warning(reason)
        return (False, reason)

    lot_size = calculate_lot_size(balance, sl_points, config.max_risk_per_trade)
    if lot_size < 0.01:
        reason = f"lot_too_small: calculated {lot_size:.4f} lots (min 0.01)"
        logger.warning(reason)
        return (False, reason)

    # ---------------------------------------------------------------
    # All checks passed
    # ---------------------------------------------------------------
    logger.info(
        f"PASS | direction={direction}, sl_points={sl_points:.0f}, "
        f"lot_size={lot_size}, daily_pnl={daily_pnl:.2f}"
    )
    return (True, "")


def calculate_lot_size(
    account_balance: float,
    sl_points: float,
    max_risk_pct: float = 0.02,
) -> float:
    """
    Calculate lot size based on 2% rule.
    Reference: ARCHITECTURE.md Section 12

    Formula:
        risk_usd = account_balance * max_risk_pct
        sl_value_per_lot = sl_points * 1.0
        lot_size = risk_usd / sl_value_per_lot
        lot_size = round(lot_size, 2)
        lot_size = max(0.01, lot_size)
    """
    if sl_points <= 0 or account_balance <= 0:
        return 0.01

    risk_usd = account_balance * max_risk_pct
    sl_value_per_lot = sl_points * 1.0
    lot_size = risk_usd / sl_value_per_lot
    lot_size = round(lot_size, 2)
    lot_size = max(0.01, lot_size)

    return lot_size


def get_sl_points(entry_price: float, sl_level: float) -> float:
    """
    Calculate SL distance in points.
    1 point = $0.01 price movement on XAUUSD.
    Reference: ARCHITECTURE.md Section 12

    sl_points = abs(entry_price - sl_level) * 100
    """
    return abs(entry_price - sl_level) * 100


def is_daily_limit_reached(db, config) -> bool:
    """Check if daily loss limit has been hit."""
    daily_pnl = db.get_daily_pnl()
    return daily_pnl <= -config.max_daily_loss_usd


def is_max_positions_reached(market_positions: list, config) -> bool:
    """Check if maximum open positions reached."""
    return len(market_positions) >= config.max_positions
