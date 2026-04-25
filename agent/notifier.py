"""
GoldTrader AI Agent — Telegram Notifications
All templates exactly as defined in ARCHITECTURE.md Section 7.
Never crashes main loop on Telegram failure.
Reference: ARCHITECTURE.md Section 7, Section 14 (circuit breaker)
"""

import logging
import requests
from typing import Optional

logger = logging.getLogger("notifier")

TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"


class Notifier:
    """Telegram notification sender. Failures are logged, never raised."""

    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.url = TELEGRAM_API.format(token=bot_token)

    def send_message(self, text: str) -> bool:
        """Send raw text message. Returns True on success."""
        try:
            resp = requests.post(
                self.url,
                json={"chat_id": self.chat_id, "text": text, "parse_mode": "HTML"},
                timeout=10,
            )
            if resp.status_code == 200:
                return True
            logger.warning(f"Telegram HTTP {resp.status_code}: {resp.text[:200]}")
            return False
        except Exception as e:
            logger.warning(f"Telegram send failed: {e}")
            return False

    # ------------------------------------------------------------------
    # A+ Executed — ARCHITECTURE.md Section 7
    # ------------------------------------------------------------------

    def send_trade_placed(self, trade: dict) -> bool:
        """Send A+ trade execution confirmation."""
        text = (
            f"🟢 TRADE PLACED\n"
            f"XAUUSD {trade.get('direction', '?')} | {trade.get('lot_size', '?')} lots\n"
            f"Entry: {trade.get('entry_price', '?')}\n"
            f"TP1: {trade.get('tp1_level', '?')}\n"
            f"TP2: {trade.get('tp2_level', '?')}\n"
            f"SL: {trade.get('sl_level', '?')}\n"
            f"Window: {trade.get('window_name', '?')}\n"
            f"Confidence: {trade.get('confidence', '?')}%\n"
            f"Reason: {trade.get('reasoning', '?')}\n"
            f"[{trade.get('account_type', 'demo')}]"
        )
        return self.send_message(text)

    # ------------------------------------------------------------------
    # B Alert — Full Parameters for Manual Entry
    # ------------------------------------------------------------------

    def send_b_alert(self, analysis: dict) -> bool:
        """Send B grade setup alert with full parameters."""
        text = (
            f"🟡 SETUP ALERT — Grade B\n\n"
            f"{analysis.get('direction', '?')} XAUUSD @ {analysis.get('entry_price', '?')}\n"
            f"TP1: {analysis.get('tp1', '?')}\n"
            f"TP2: {analysis.get('tp2', '?')}\n"
            f"SL:  {analysis.get('sl', '?')}\n\n"
            f"Window: {analysis.get('window', '?')}\n"
            f"Invalidation: {analysis.get('invalidation', '?')}\n"
            f"Reason: {analysis.get('reasoning', '?')}\n\n"
            f"Manual execution only"
        )
        return self.send_message(text)

    # ------------------------------------------------------------------
    # GPT Challenge (downgraded from A+)
    # ------------------------------------------------------------------

    def send_gpt_challenge(self, analysis: dict) -> bool:
        """Send GPT challenge notification."""
        text = (
            f"🔶 SETUP DOWNGRADED — A+ → B\n"
            f"Claude: A+ | GPT: CHALLENGE\n\n"
            f"{analysis.get('direction', '?')} XAUUSD @ {analysis.get('entry_price', '?')}\n"
            f"TP1: {analysis.get('tp1', '?')}\n"
            f"TP2: {analysis.get('tp2', '?')}\n"
            f"SL:  {analysis.get('sl', '?')}\n\n"
            f"GPT concern: {analysis.get('gpt_reasoning', '?')}\n"
            f"Manual execution only"
        )
        return self.send_message(text)

    # ------------------------------------------------------------------
    # Risk Blocked
    # ------------------------------------------------------------------

    def send_risk_blocked(self, reason: str, decision_id: int) -> bool:
        """Send risk block notification."""
        text = (
            f"🔴 TRADE BLOCKED\n"
            f"Grade: A+ | GPT: CONFIRMED\n"
            f"Blocked by: {reason}\n\n"
            f"Setup preserved in log ID: {decision_id}"
        )
        return self.send_message(text)

    # ------------------------------------------------------------------
    # News Alert
    # ------------------------------------------------------------------

    def send_news_alert(self, news_summary: str) -> bool:
        """Send high-risk news skip notification."""
        text = (
            f"⚠️ NEWS ALERT — SETUP SKIPPED\n"
            f"Risk: HIGH\n"
            f"{news_summary}\n\n"
            f"Next check at next M15 close"
        )
        return self.send_message(text)

    # ------------------------------------------------------------------
    # Skip
    # ------------------------------------------------------------------

    def send_skip(self, reason: str) -> bool:
        """Send skip notification."""
        text = f"⚪ SKIPPED\n{reason}"
        return self.send_message(text)

    # ------------------------------------------------------------------
    # TP1 Hit
    # ------------------------------------------------------------------

    def send_tp1_hit(self, trade: dict) -> bool:
        """Send TP1 hit notification."""
        text = (
            f"💰 TP1 HIT\n"
            f"XAUUSD {trade.get('direction', '?')} | Ticket: {trade.get('ticket_id', '?')}\n"
            f"TP1: {trade.get('tp1_price', '?')} reached\n"
            f"SL moved to breakeven: {trade.get('entry_price', '?')}\n"
            f"Runner targeting TP2: {trade.get('tp2_price', '?')}\n"
            f"[{trade.get('account_type', 'demo')}]"
        )
        return self.send_message(text)

    # ------------------------------------------------------------------
    # Window Open
    # ------------------------------------------------------------------

    def send_window_open(self, window_name: str, session: str, price: float) -> bool:
        """Send window open notification."""
        text = (
            f"📍 WINDOW OPEN — {window_name}\n"
            f"Session: {session}\n"
            f"XAUUSD: {price:.2f}\n"
            f"Watching for setups..."
        )
        return self.send_message(text)

    # ------------------------------------------------------------------
    # Claude SKIP (called only when Claude actually analysed, not prefilter)
    # ------------------------------------------------------------------

    def send_claude_skip(self, analysis: dict, price: float, price_pos: float) -> bool:
        """Send Claude SKIP notification with condensed reasoning."""
        pillars = []
        for p, label in [
            ("pillar_trend", "Trend"),
            ("pillar_momentum", "Mom"),
            ("pillar_structure", "Str"),
        ]:
            val = analysis.get(p, "?")
            pillars.append(f"{label}:{val}")

        text = (
            f"⚪ SKIP — {analysis.get('direction', 'WAIT')} | "
            f"Conf:{analysis.get('confidence', 0)}%\n"
            f"Price: {price:.2f} ({price_pos:.0f}% range)\n"
            f"{' | '.join(pillars)}\n"
            f"{analysis.get('skip_reason', '—')}"
        )
        return self.send_message(text)

    # ------------------------------------------------------------------
    # Session Digest (sent at window close)
    # ------------------------------------------------------------------

    def send_session_digest(self, digest: dict) -> bool:
        """Send end-of-window session digest."""
        window_name = digest.get("window_name", "?")
        session_date = digest.get("date", "?")
        cycles = digest.get("total_cycles", 0)
        pf_pass = digest.get("prefilter_pass", 0)
        claude_called = digest.get("claude_called", 0)
        trades = digest.get("trades_taken", 0)
        pnl = digest.get("session_pnl", 0.0)
        high = digest.get("session_high", 0)
        low = digest.get("session_low", 0)
        rng = round(high - low, 2) if high and low else 0
        character = digest.get("character", "—")
        skip_reasons = digest.get("top_skip_reasons", [])

        trade_line = ""
        if trades > 0:
            sign = "+" if pnl >= 0 else ""
            trade_line = f"Trades: {trades} | PnL: {sign}${pnl:.2f}\n"
        else:
            trade_line = "Trades: 0 — no setup executed\n"

        reasons_line = ""
        if skip_reasons:
            reasons_line = f"Top skips: {', '.join(skip_reasons)}\n"

        text = (
            f"📊 SESSION DIGEST — {window_name}\n"
            f"{session_date}\n\n"
            f"Range: {low:.2f} – {high:.2f} ({rng:.0f}pts)\n"
            f"Character: {character}\n\n"
            f"Cycles: {cycles} | PF pass: {pf_pass} | Claude: {claude_called}\n"
            f"{trade_line}"
            f"{reasons_line}"
        )
        return self.send_message(text)

    # ------------------------------------------------------------------
    # Agent Status
    # ------------------------------------------------------------------

    def send_agent_status(self, status: str) -> bool:
        """Send agent lifecycle notification (startup/shutdown)."""
        text = f"🤖 AGENT: {status}"
        return self.send_message(text)
