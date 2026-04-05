"""
GoldTrader AI Agent — Context Builder
Builds the full context package sent to Claude as the user message.
Reference: PLAYBOOK.md Context Package section, ARCHITECTURE.md Section 3
"""

import logging
from datetime import datetime, timezone

logger = logging.getLogger("context")


def build_context(
    indicators: dict,
    window_status: dict,
    account_info: dict,
    news_context: dict,
    db,
) -> dict:
    """
    Build the full context package matching PLAYBOOK.md spec.
    This dict is serialized and sent as the user message to Claude.

    Args:
        indicators: {H4, H1, M30, M15, session_levels, current_price, m30_sequence}
        window_status: {window, minutes_into_window, session}
        account_info: {balance, equity, margin_free, profit}
        news_context: from news.get_news_context()
        db: Database instance

    Returns:
        Full context dict matching PLAYBOOK.md "Context Package You Receive"
    """

    # Current price and spread
    current_price = indicators.get("current_price", 0)
    spread = indicators.get("spread", 0)

    # Session levels
    session = indicators.get("session_levels", {})

    # Price position
    session_high = session.get("session_high", 0)
    session_low = session.get("session_low", 0)
    if session_high > session_low and current_price > 0:
        price_position_pct = round(
            ((current_price - session_low) / (session_high - session_low)) * 100, 1
        )
    else:
        price_position_pct = 50.0

    # ATR values for context
    h1_data = indicators.get("H1", {})
    m15_data = indicators.get("M15", {})

    # Recent history from database
    recent_decisions = db.get_recent_decisions(n=5)
    recent_trades = db.get_recent_trades(n=3)
    daily_pnl = db.get_daily_pnl()
    open_positions_count = db.get_open_positions_count()

    # Simplify decisions for context (remove noise)
    decisions_summary = []
    for d in recent_decisions:
        decisions_summary.append({
            "grade": d.get("grade"),
            "direction": d.get("direction"),
            "confidence": d.get("confidence"),
            "executed": d.get("executed"),
            "skip_reason": d.get("skip_reason"),
            "timestamp": d.get("timestamp"),
        })

    # Simplify trades for context
    trades_summary = []
    for t in recent_trades:
        trades_summary.append({
            "direction": t.get("direction"),
            "profit_usd": t.get("profit_usd"),
            "exit_reason": t.get("exit_reason"),
            "timestamp_open": t.get("timestamp_open"),
        })

    # Build the context package (matches PLAYBOOK.md exactly)
    context = {
        # Market data
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "session": window_status.get("session", "UNKNOWN"),
        "window_status": window_status.get("window", "OUTSIDE"),
        "minutes_into_window": window_status.get("minutes_into_window", 0),
        "current_price": current_price,
        "spread": spread,
        "atr_current": h1_data.get("atr", 0),
        "atr_average": indicators.get("atr_average", 0),

        # H4 indicators
        "h4": {
            "direction": indicators.get("H4", {}).get("direction", "NEUTRAL"),
            "strength": indicators.get("H4", {}).get("strength", 0),
            "rsi": indicators.get("H4", {}).get("rsi", 50),
            "macd": indicators.get("H4", {}).get("macd", {}),
            "macd_slope": indicators.get("H4", {}).get("macd", {}).get("slope", "flat"),
        },

        # H1 indicators
        "h1": {
            "direction": indicators.get("H1", {}).get("direction", "NEUTRAL"),
            "strength": indicators.get("H1", {}).get("strength", 0),
            "rsi": indicators.get("H1", {}).get("rsi", 50),
            "macd": indicators.get("H1", {}).get("macd", {}),
            "macd_slope": indicators.get("H1", {}).get("macd", {}).get("slope", "flat"),
        },

        # M30 indicators
        "m30": {
            "last_5_candles": indicators.get("m30_sequence", []),
            "dominant_direction": indicators.get("M30", {}).get("direction", "NEUTRAL"),
            "body_strength_ratio": indicators.get("M30", {}).get("body_ratio", 0),
            "volatility_description": _describe_volatility(
                indicators.get("M30", {}).get("atr", 0),
                indicators.get("atr_average", 0),
            ),
            "momentum_quality": _describe_momentum(indicators.get("M30", {})),
        },

        # M15 indicators
        "m15": {
            "direction": indicators.get("M15", {}).get("direction", "NEUTRAL"),
            "strength": indicators.get("M15", {}).get("strength", 0),
            "rsi": indicators.get("M15", {}).get("rsi", 50),
            "last_closed_price": indicators.get("M15", {}).get("last_close", current_price),
            "body_ratio": indicators.get("M15", {}).get("body_ratio", 0),
        },

        # Session levels
        "session_high": session.get("session_high", 0),
        "session_low": session.get("session_low", 0),
        "price_position_pct": price_position_pct,
        "asia_high": session.get("asia_high", 0),
        "asia_low": session.get("asia_low", 0),

        # Account context (number only, no label — AI isolation)
        "account_balance": account_info.get("balance", 0),
        "daily_pnl": daily_pnl,
        "open_positions_count": open_positions_count,

        # Recent history
        "last_5_decisions": decisions_summary,
        "last_3_trades": trades_summary,

        # News context
        "calendar_events_next_60min": news_context.get("calendar_events", []),
        "perplexity_summary": news_context.get("summary") if news_context.get("source") == "perplexity" else None,
        "news_risk_level": news_context.get("risk_level", "LOW"),
    }

    logger.debug(f"Context built: window={context['window_status']}, price={context['current_price']}")
    return context


def _describe_volatility(current_atr: float, avg_atr: float) -> str:
    """Human-readable volatility description for Claude."""
    if avg_atr <= 0:
        return "unknown"
    ratio = current_atr / avg_atr
    if ratio > 2.0:
        return "extremely high (anomalous)"
    elif ratio > 1.5:
        return "high"
    elif ratio > 0.8:
        return "normal"
    elif ratio > 0.5:
        return "low"
    else:
        return "very low (compressed)"


def _describe_momentum(m30_data: dict) -> str:
    """Human-readable momentum quality for Claude."""
    body_ratio = m30_data.get("body_ratio", 0)
    macd = m30_data.get("macd", {})
    slope = macd.get("slope", "flat")

    if body_ratio > 65 and slope == "expanding":
        return "strong and building"
    elif body_ratio > 60:
        return "solid"
    elif body_ratio > 55 and slope == "expanding":
        return "borderline improving"
    elif 40 <= body_ratio <= 55:
        return "indecisive (dead zone)"
    elif body_ratio < 40 and slope == "contracting":
        return "weak and fading"
    elif body_ratio < 40:
        return "weak"
    else:
        return "moderate"
