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
    # Agent Status
    # ------------------------------------------------------------------

    def send_agent_status(self, status: str) -> bool:
        """Send agent lifecycle notification (startup/shutdown)."""
        text = f"🤖 AGENT: {status}"
        return self.send_message(text)
