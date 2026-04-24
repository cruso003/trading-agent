"""
GoldTrader AI Agent — Main Loop
Entry point and orchestration. Follows ARCHITECTURE.md Section 3 pipeline exactly.
Reference: ARCHITECTURE.md Section 3, Section 13, Section 14, Section 15
"""

import argparse
import logging
import logging.handlers
import signal
import sys
import time
import json
from datetime import datetime, timezone
from pathlib import Path

# Agent modules
from agent.config import load_config
from agent.database import Database
from agent.windows import (
    get_current_window, is_tradeable_time, minutes_into_window,
    time_to_next_window, get_window_name, get_current_session,
)
from agent.market import Market
from agent.indicators import (
    analyse_timeframe, get_session_levels, get_price_position,
    get_m30_sequence, get_m15_swings, calculate_atr,
)
from agent.prefilter import run_prefilter
from agent.news import get_news_context
from agent.context import build_context
from agent.claude_agent import ClaudeAgent
from agent.gpt_agent import GPTAgent
from agent.risk import validate as risk_validate, calculate_lot_size, get_sl_points
from agent.executor import Executor
from agent.notifier import Notifier


# ------------------------------------------------------------------
# Logging setup (ARCHITECTURE.md Section 15)
# ------------------------------------------------------------------

def setup_logging(log_level: str, project_root: Path, debug: bool = False):
    """Configure structured logging with daily rotation."""
    log_dir = project_root / "agent" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    # Root logger
    root_logger = logging.getLogger()
    level = logging.DEBUG if debug else getattr(logging, log_level, logging.INFO)
    root_logger.setLevel(level)

    # Format: {timestamp} | {level} | {module} | {message}
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # File handler: daily rotation, 30 day retention
    file_handler = logging.handlers.TimedRotatingFileHandler(
        log_dir / "agent.log",
        when="midnight",
        backupCount=30,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    file_handler.suffix = "%Y-%m-%d"
    root_logger.addHandler(file_handler)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    return logging.getLogger("main")


# ------------------------------------------------------------------
# Graceful shutdown
# ------------------------------------------------------------------

_shutdown_requested = False


def _signal_handler(signum, frame):
    global _shutdown_requested
    _shutdown_requested = True
    print("\nShutdown requested. Finishing current cycle...")


# ------------------------------------------------------------------
# Main Loop
# ------------------------------------------------------------------

def main():
    """
    Main entry point. Orchestrates the full pipeline:
    MT5 → indicators → windows → prefilter → news → context →
    claude → gpt → risk → executor → database → notifier → sleep
    """
    global _shutdown_requested

    # Parse CLI arguments
    parser = argparse.ArgumentParser(description="GoldTrader AI Agent")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--dry-run", action="store_true", help="Run pipeline without executing trades")
    args = parser.parse_args()

    # Load config
    config = load_config()

    # Setup logging
    logger = setup_logging(config.log_level, config.project_root, debug=args.debug)
    logger.info("=" * 60)
    logger.info("GoldTrader AI Agent starting")
    logger.info(f"Account: {config.active_account}")
    logger.info(f"Symbol: {config.symbol}")
    logger.info(f"Claude model: {config.claude_model}")
    logger.info(f"GPT model: {config.gpt_model}")
    if args.dry_run:
        logger.info("*** DRY RUN MODE — no trades will be executed ***")
    logger.info("=" * 60)

    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    # Initialize components
    db = Database(config.db_full_path)
    market = Market()
    notifier = Notifier(config.telegram_bot_token, config.telegram_chat_id)
    executor = Executor(market, db, notifier, config)

    # Initialize AI agents
    claude = ClaudeAgent(config.anthropic_api_key, config.claude_model, config.playbook_path)
    gpt = GPTAgent(config.openai_api_key, config.gpt_model)

    # Connect to MT5
    logger.info("Connecting to MT5...")
    mt5_connected = market.connect(config.mt5_login, config.mt5_password, config.mt5_server)
    if not mt5_connected:
        logger.critical("Failed to connect to MT5. Exiting.")
        notifier.send_agent_status("STARTUP FAILED — MT5 connection error")
        sys.exit(1)

    # Startup notification
    notifier.send_agent_status(f"STARTED [{config.active_account}]")
    db.update_agent_state({"status": "watching"})

    # ---------------------------------------------------------------
    # MAIN LOOP
    # ---------------------------------------------------------------

    # Session tracker — reset each time we enter a new window
    _session = {
        "window": None,
        "start_time": None,
        "total_cycles": 0,
        "prefilter_pass": 0,
        "claude_called": 0,
        "trades_taken": 0,
        "session_pnl": 0.0,
        "session_high": 0.0,
        "session_low": float("inf"),
        "h4_direction": "NEUTRAL",
        "skip_reasons": [],
        "open_notified": False,
    }

    def _reset_session(window_id, window_name):
        _session["window"] = window_id
        _session["window_name"] = window_name
        _session["start_time"] = datetime.now(timezone.utc).isoformat()
        _session["total_cycles"] = 0
        _session["prefilter_pass"] = 0
        _session["claude_called"] = 0
        _session["trades_taken"] = 0
        _session["session_pnl"] = 0.0
        _session["session_high"] = 0.0
        _session["session_low"] = float("inf")
        _session["h4_direction"] = "NEUTRAL"
        _session["skip_reasons"] = []
        _session["open_notified"] = False

    def _flush_session_digest(window_id, session_label, current_price):
        """Write session summary to DB and send Telegram digest."""
        if _session["window"] != window_id:
            return
        if _session["total_cycles"] == 0:
            return

        high = _session["session_high"] if _session["session_high"] > 0 else current_price
        low = _session["session_low"] if _session["session_low"] < float("inf") else current_price
        rng = round(high - low, 2)

        # Classify character
        if rng > 120:
            character = "VOLATILE"
        elif rng > 80:
            character = "TRENDING"
        elif rng < 40:
            character = "COMPRESSING"
        else:
            character = "RANGING"

        # Top skip reasons (most common, max 3)
        from collections import Counter
        reason_counts = Counter(_session["skip_reasons"])
        top_reasons = [r for r, _ in reason_counts.most_common(3)]

        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        digest = {
            "date": today,
            "window_name": window_id,
            "session_label": session_label,
            "window_start": _session.get("start_time", ""),
            "window_end": datetime.now(timezone.utc).isoformat(),
            "session_high": round(high, 2),
            "session_low": round(low, 2),
            "range_pts": rng,
            "character": character,
            "total_cycles": _session["total_cycles"],
            "prefilter_pass": _session["prefilter_pass"],
            "claude_called": _session["claude_called"],
            "trades_taken": _session["trades_taken"],
            "session_pnl": round(_session["session_pnl"], 2),
            "top_skip_reasons": json.dumps(top_reasons),
            "h4_direction": _session["h4_direction"],
            "notes": None,
        }

        db.save_session_summary(digest)

        digest["window_name"] = get_window_name(
            window_id,
            config.window_1_start, config.window_1_end,
            config.window_2_start, config.window_2_end,
        )
        digest["top_skip_reasons"] = top_reasons
        notifier.send_session_digest(digest)
        logger.info(f"Session digest sent: {character}, range={rng}pts")

    try:
        while not _shutdown_requested:
            cycle_start = datetime.now(timezone.utc)
            logger.info("-" * 40)

            # ----------------------------------------------------------
            # Step 1: Check trading windows (BEFORE any data fetch)
            # ----------------------------------------------------------
            window = get_current_window(
                config.window_1_start, config.window_1_end,
                config.window_2_start, config.window_2_end,
            )

            if window is None:
                # Flush digest if we just left a window
                if _session["window"] is not None:
                    price_now = 0.0
                    try:
                        pi = market.get_current_price(symbol=config.symbol)
                        price_now = pi.get("bid", 0.0)
                    except Exception:
                        pass
                    _flush_session_digest(
                        _session["window"],
                        get_current_session(),
                        price_now,
                    )
                    _session["window"] = None

                next_w = time_to_next_window(
                    config.window_1_start, config.window_1_end,
                    config.window_2_start, config.window_2_end,
                )
                # Sleep until 1 minute before next window — wake up ready, not polling
                sleep_minutes = max(1, next_w['minutes'] - 1)
                logger.info(
                    f"Outside windows. Next: {next_w['window']} in {next_w['minutes']}min "
                    f"— sleeping {sleep_minutes}min"
                )
                db.update_agent_state({"status": "sleeping", "current_window": "OUTSIDE"})
                # Sleep in 1s ticks so shutdown is still responsive
                for _ in range(sleep_minutes * 60):
                    if _shutdown_requested:
                        break
                    time.sleep(1)
                continue

            session = get_current_session()
            mins_in = minutes_into_window(
                config.window_1_start, config.window_1_end,
                config.window_2_start, config.window_2_end,
            )
            window_status = {
                "window": window,
                "minutes_into_window": mins_in,
                "session": session,
            }
            win_display = get_window_name(window, config.window_1_start, config.window_1_end, config.window_2_start, config.window_2_end)
            logger.info(f"WINDOW: {win_display} | {mins_in}min in | session={session}")
            db.update_agent_state({"status": "watching", "current_window": window})

            # New window entered — reset tracker and send open ping
            if _session["window"] != window:
                _reset_session(window, win_display)

            # Window open ping (once per window entry)
            if not _session["open_notified"]:
                try:
                    pi = market.get_current_price(symbol=config.symbol)
                    open_price = pi.get("bid", 0.0)
                except Exception:
                    open_price = 0.0
                notifier.send_window_open(win_display, session, open_price)
                _session["open_notified"] = True

            # ----------------------------------------------------------
            # Step 2: Check MT5 connection (circuit breaker)
            # ----------------------------------------------------------
            if not market.is_connected():
                logger.warning("MT5 disconnected, attempting reconnect...")
                reconnected = False
                for attempt in range(5):
                    if market.connect(config.mt5_login, config.mt5_password, config.mt5_server):
                        logger.info("MT5 reconnected")
                        reconnected = True
                        break
                    logger.warning(f"Reconnect attempt {attempt + 1}/5 failed")
                    time.sleep(60)

                if not reconnected:
                    logger.critical("MT5 reconnect failed after 5 attempts")
                    notifier.send_agent_status("CRITICAL — MT5 disconnected, retrying in 5 min")
                    time.sleep(300)
                    continue

            # ----------------------------------------------------------
            # Step 3: Fetch market data
            # ----------------------------------------------------------
            logger.info("Fetching market data...")
            sym = config.symbol
            candles_h4 = market.get_candles(symbol=sym, timeframe="H4", count=50)
            candles_h1 = market.get_candles(symbol=sym, timeframe="H1", count=60)
            candles_m30 = market.get_candles(symbol=sym, timeframe="M30", count=30)
            candles_m15 = market.get_candles(symbol=sym, timeframe="M15", count=30)
            price_info = market.get_current_price(symbol=sym)
            account_info = market.get_account_info()
            open_positions = market.get_open_positions(symbol=sym, magic=config.magic_number)

            if not candles_m15 or not price_info:
                logger.warning("No market data available, sleeping 60s")
                time.sleep(60)
                continue

            current_price = price_info.get("bid", 0)

            # ----------------------------------------------------------
            # Step 4: Calculate indicators
            # ----------------------------------------------------------
            logger.info("Calculating indicators...")
            h4_data = analyse_timeframe(candles_h4, "H4")
            h1_data = analyse_timeframe(candles_h1, "H1")
            m30_data = analyse_timeframe(candles_m30, "M30")
            m15_data = analyse_timeframe(candles_m15, "M15")

            session_levels = get_session_levels(candles_h1)
            m30_sequence = get_m30_sequence(candles_m30, count=5)
            m15_swings = get_m15_swings(candles_m15, lookback=10)

            # ATR average for anomaly detection
            atr_average = calculate_atr(candles_h1, period=20) if len(candles_h1) >= 21 else h1_data["atr"]

            indicators = {
                "H4": h4_data,
                "H1": h1_data,
                "M30": m30_data,
                "M15": m15_data,
                "session_levels": session_levels,
                "current_price": current_price,
                "spread": price_info.get("spread", 0),
                "m30_sequence": m30_sequence,
                "m15_swings": m15_swings,
                "atr_average": atr_average,
            }

            # ----------------------------------------------------------
            # Step 5: Prefilter (zero API cost)
            # ----------------------------------------------------------
            # Track session high/low and H4 direction
            _session["total_cycles"] += 1
            if current_price > _session["session_high"]:
                _session["session_high"] = current_price
            if current_price < _session["session_low"]:
                _session["session_low"] = current_price
            _session["h4_direction"] = h4_data.get("direction", "NEUTRAL")

            logger.info("Running prefilter...")
            pf_passed, pf_reason = run_prefilter(
                indicators, window_status, open_positions, db, config
            )

            if not pf_passed:
                logger.info(f"Prefilter FAIL: {pf_reason}")
                # Track prefilter skip reason category
                reason_key = pf_reason.split(":")[0]
                _session["skip_reasons"].append(reason_key)
                market.wait_for_next_m15(stop_check=lambda: _shutdown_requested)
                continue

            _session["prefilter_pass"] += 1

            logger.info("Prefilter PASS — proceeding to news check")

            # ----------------------------------------------------------
            # Step 5: News check
            # ----------------------------------------------------------
            logger.info("Checking news context...")
            calendar_events = market.get_economic_calendar(hours_ahead=1)
            news_context = get_news_context(
                calendar_events=calendar_events,
                current_atr=h1_data["atr"],
                avg_atr=atr_average,
                perplexity_api_key=config.perplexity_api_key,
                cache_minutes=config.news_cache_minutes,
            )

            if news_context["should_skip"]:
                logger.info(f"News SKIP: {news_context['summary']}")
                notifier.send_news_alert(news_context["summary"])
                market.wait_for_next_m15(stop_check=lambda: _shutdown_requested)
                continue

            logger.info(f"News OK: risk={news_context['risk_level']}")

            # ----------------------------------------------------------
            # Step 6: Build context package
            # ----------------------------------------------------------
            logger.info("Building context package...")
            ctx = build_context(indicators, window_status, account_info, news_context, db)

            # ----------------------------------------------------------
            # Step 7: Claude analysis
            # ----------------------------------------------------------
            logger.info("Calling Claude for analysis...")
            db.update_agent_state({"status": "analysing", "last_analysis_time": datetime.now(timezone.utc).isoformat()})
            _session["claude_called"] += 1

            analysis = claude.analyse(ctx)
            grade = analysis.get("grade", "SKIP")
            direction = analysis.get("direction", "WAIT")

            logger.info(f"Claude: grade={grade}, direction={direction}, confidence={analysis.get('confidence', 0)}")

            # Log decision to database
            decision_record = {
                "window_name": window,
                "grade": grade,
                "direction": direction,
                "entry_price": analysis.get("entry_price"),
                "entry_zone": analysis.get("entry_zone"),
                "sl_level": analysis.get("sl"),
                "tp1_level": analysis.get("tp1"),
                "tp2_level": analysis.get("tp2"),
                "invalidation": analysis.get("invalidation"),
                "reasoning": analysis.get("reasoning"),
                "confidence": analysis.get("confidence"),
                "pillar_trend": analysis.get("pillar_trend"),
                "pillar_momentum": analysis.get("pillar_momentum"),
                # DB column retains legacy name `pillar_location` for row
                # compatibility; PLAYBOOK v2.0 renames this to pillar_structure.
                "pillar_location": analysis.get("pillar_structure"),
                "setup_type": analysis.get("setup_type"),
                # DB column `base_zone` now stores the M15 swing SL reference.
                "base_zone": analysis.get("m15_swing_ref"),
                "news_risk": news_context.get("risk_level"),
                "news_summary": news_context.get("summary"),
                "skip_reason": analysis.get("skip_reason"),
            }

            # ----------------------------------------------------------
            # Handle SKIP
            # ----------------------------------------------------------
            if grade == "SKIP":
                decision_record["executed"] = False
                db.log_decision(decision_record)
                logger.info(f"SKIP: {analysis.get('skip_reason', 'No reason')}")
                _session["skip_reasons"].append("claude_skip")
                # Send Claude SKIP to Telegram
                price_pos = ctx.get("price_position_pct", 0.0)
                notifier.send_claude_skip(analysis, current_price, price_pos)
                market.wait_for_next_m15(stop_check=lambda: _shutdown_requested)
                continue

            # ----------------------------------------------------------
            # Handle B grade — alert only, no execution
            # ----------------------------------------------------------
            if grade == "B":
                decision_record["executed"] = False
                db.log_decision(decision_record)
                notifier.send_b_alert(analysis)
                logger.info("Grade B — Telegram alert sent, no execution")
                market.wait_for_next_m15(stop_check=lambda: _shutdown_requested)
                continue

            # ----------------------------------------------------------
            # Step 8: A+ — GPT second opinion
            # ----------------------------------------------------------
            logger.info("A+ detected — calling GPT for second opinion...")
            gpt_result = gpt.verify(ctx, analysis)
            verdict = gpt_result["verdict"]
            gpt_reasoning = gpt_result["reasoning"]

            decision_record["gpt_verdict"] = verdict
            decision_record["gpt_reasoning"] = gpt_reasoning

            logger.info(f"GPT: {verdict} — {gpt_reasoning[:80]}")

            if verdict == "CHALLENGE":
                decision_record["executed"] = False
                decision_id = db.log_decision(decision_record)
                analysis["gpt_reasoning"] = gpt_reasoning
                notifier.send_gpt_challenge(analysis)
                logger.info("GPT CHALLENGE — downgraded to B, alert sent")
                market.wait_for_next_m15(stop_check=lambda: _shutdown_requested)
                continue

            # ----------------------------------------------------------
            # Step 9: Risk validation
            # ----------------------------------------------------------
            logger.info("Running risk validation...")
            risk_passed, risk_reason = risk_validate(
                direction=direction,
                entry_price=analysis["entry_price"],
                sl_level=analysis["sl"],
                db=db,
                account_info=account_info,
                market_positions=open_positions,
                config=config,
            )

            if not risk_passed:
                decision_record["executed"] = False
                decision_record["execution_reason"] = risk_reason
                decision_id = db.log_decision(decision_record)
                notifier.send_risk_blocked(risk_reason, decision_id)
                logger.info(f"Risk BLOCKED: {risk_reason}")
                market.wait_for_next_m15(stop_check=lambda: _shutdown_requested)
                continue

            # ----------------------------------------------------------
            # Step 10: Execute trade
            # ----------------------------------------------------------
            sl_points = get_sl_points(analysis["entry_price"], analysis["sl"])
            lot_size = calculate_lot_size(
                account_info.get("balance", 0),
                sl_points,
                config.max_risk_per_trade,
            )

            if args.dry_run:
                logger.info(f"DRY RUN — would execute: {direction} {lot_size} lots")
                decision_record["executed"] = False
                decision_record["execution_reason"] = "dry_run"
                db.log_decision(decision_record)
                market.wait_for_next_m15(stop_check=lambda: _shutdown_requested)
                continue

            logger.info(f"EXECUTING: {direction} {lot_size} lots, SL={analysis['sl']}, TP1={analysis['tp1']}, TP2={analysis['tp2']}")
            db.update_agent_state({"status": "executing"})

            success, ticket_id, error = executor.place_trade(
                direction=direction,
                lot_size=lot_size,
                sl=analysis["sl"],
                tp1=analysis["tp1"],
                tp2=analysis["tp2"],
                comment=f"GT_{window}_{grade}",
            )

            if success:
                decision_record["executed"] = True
                decision_id = db.log_decision(decision_record)
                _session["trades_taken"] += 1

                # Log trade
                db.log_trade({
                    "ticket_id": ticket_id,
                    "direction": direction,
                    "lot_size": lot_size,
                    "entry_price": analysis["entry_price"],
                    "sl_price": analysis["sl"],
                    "tp1_price": analysis["tp1"],
                    "tp2_price": analysis["tp2"],
                    "account_type": config.active_account,
                    "decision_id": decision_id,
                })

                # Telegram confirmation
                notifier.send_trade_placed({
                    "direction": direction,
                    "lot_size": lot_size,
                    "entry_price": analysis["entry_price"],
                    "tp1_level": analysis["tp1"],
                    "tp2_level": analysis["tp2"],
                    "sl_level": analysis["sl"],
                    "window_name": get_window_name(window, config.window_1_start, config.window_1_end, config.window_2_start, config.window_2_end),
                    "confidence": analysis.get("confidence"),
                    "reasoning": analysis.get("reasoning"),
                    "account_type": config.active_account,
                })

                logger.info(f"Trade placed: ticket={ticket_id}")
                db.update_agent_state({
                    "status": "watching",
                    "last_trade_time": datetime.now(timezone.utc).isoformat(),
                })

            else:
                decision_record["executed"] = False
                decision_record["execution_reason"] = f"MT5 error: {error}"
                db.log_decision(decision_record)
                logger.error(f"Trade execution failed: {error}")

            # ----------------------------------------------------------
            # Sleep until next M15
            # ----------------------------------------------------------
            market.wait_for_next_m15(stop_check=lambda: _shutdown_requested)

    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received")
    except Exception as e:
        logger.critical(f"Unexpected error in main loop: {e}", exc_info=True)
    finally:
        # Cleanup
        logger.info("Shutting down...")
        db.update_agent_state({"status": "shutdown"})
        notifier.send_agent_status(f"SHUTDOWN [{config.active_account}]")
        market.disconnect()
        db.close()
        logger.info("GoldTrader AI Agent stopped")


if __name__ == "__main__":
    main()
