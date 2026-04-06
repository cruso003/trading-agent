"""
GoldTrader AI Agent — API State
Shared state bridge between agent core and FastAPI gateway.
Reads from the same SQLite database the agent writes to.
Reference: ARCHITECTURE.md Section 6, Section 11
"""

import json
import time
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from agent.database import Database


class AgentState:
    """
    Shared state layer.
    Reads from SQLite (written by agent) and holds ephemeral runtime state.
    SSE events are pushed here by the agent and consumed by the stream endpoint.
    """

    def __init__(self, db: Database):
        self.db = db
        self._sse_listeners: list = []
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # SSE Event Bus
    # ------------------------------------------------------------------

    def push_event(self, event_type: str, data: dict):
        """Push an SSE event to all connected listeners."""
        event = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        with self._lock:
            dead = []
            for queue in self._sse_listeners:
                try:
                    queue.append(event)
                except Exception:
                    dead.append(queue)
            for d in dead:
                self._sse_listeners.remove(d)

    def subscribe(self) -> list:
        """Create a new SSE listener queue. Returns the queue."""
        queue = []
        with self._lock:
            self._sse_listeners.append(queue)
        return queue

    def unsubscribe(self, queue: list):
        """Remove an SSE listener queue."""
        with self._lock:
            if queue in self._sse_listeners:
                self._sse_listeners.remove(queue)

    # ------------------------------------------------------------------
    # Agent Status (reads agent_state table)
    # ------------------------------------------------------------------

    def get_status(self) -> dict:
        """Get current agent status from database."""
        state = self.db.get_agent_state()
        return {
            "status": state.get("status", "unknown"),
            "current_window": state.get("current_window"),
            "last_analysis_time": state.get("last_analysis_time"),
            "last_trade_time": state.get("last_trade_time"),
            "daily_pnl": state.get("daily_pnl", 0),
            "updated_at": state.get("updated_at"),
        }

    # ------------------------------------------------------------------
    # Decisions
    # ------------------------------------------------------------------

    def get_decisions(self, limit: int = 50, grade: Optional[str] = None) -> list:
        """Get decision log with optional grade filter."""
        decisions = self.db.get_recent_decisions(n=limit)
        if grade:
            decisions = [d for d in decisions if d.get("grade") == grade]
        return decisions

    # ------------------------------------------------------------------
    # Trades
    # ------------------------------------------------------------------

    def get_trades(self, limit: int = 50) -> list:
        """Get trade history."""
        return self.db.get_recent_trades(n=limit)

    def get_trade(self, trade_id: int) -> Optional[dict]:
        """Get single trade by ID."""
        try:
            cursor = self.db._conn.execute(
                "SELECT * FROM agent_trades WHERE id = ?", (trade_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
        except Exception:
            return None

    # ------------------------------------------------------------------
    # Analytics
    # ------------------------------------------------------------------

    def get_analytics_summary(self) -> dict:
        """Overall performance metrics."""
        try:
            conn = self.db._conn

            # Total trades
            total = conn.execute("SELECT COUNT(*) FROM agent_trades WHERE timestamp_close IS NOT NULL").fetchone()[0]
            wins = conn.execute("SELECT COUNT(*) FROM agent_trades WHERE profit_usd > 0").fetchone()[0]
            losses = conn.execute("SELECT COUNT(*) FROM agent_trades WHERE profit_usd < 0").fetchone()[0]
            total_pnl = conn.execute("SELECT COALESCE(SUM(profit_usd), 0) FROM agent_trades WHERE timestamp_close IS NOT NULL").fetchone()[0]
            avg_profit = conn.execute("SELECT COALESCE(AVG(profit_usd), 0) FROM agent_trades WHERE profit_usd > 0").fetchone()[0]
            avg_loss = conn.execute("SELECT COALESCE(AVG(profit_usd), 0) FROM agent_trades WHERE profit_usd < 0").fetchone()[0]

            # Total decisions
            total_decisions = conn.execute("SELECT COUNT(*) FROM agent_decisions").fetchone()[0]
            a_plus = conn.execute("SELECT COUNT(*) FROM agent_decisions WHERE grade = 'A+'").fetchone()[0]
            b_grade = conn.execute("SELECT COUNT(*) FROM agent_decisions WHERE grade = 'B'").fetchone()[0]
            skips = conn.execute("SELECT COUNT(*) FROM agent_decisions WHERE grade = 'SKIP'").fetchone()[0]

            # GPT challenges
            challenges = conn.execute("SELECT COUNT(*) FROM agent_decisions WHERE gpt_verdict = 'CHALLENGE'").fetchone()[0]

            return {
                "total_trades": total,
                "wins": wins,
                "losses": losses,
                "win_rate": round(wins / total * 100, 1) if total > 0 else 0,
                "total_pnl": round(total_pnl, 2),
                "avg_win": round(avg_profit, 2),
                "avg_loss": round(avg_loss, 2),
                "profit_factor": round(abs(avg_profit / avg_loss), 2) if avg_loss != 0 else 0,
                "total_decisions": total_decisions,
                "a_plus_count": a_plus,
                "b_count": b_grade,
                "skip_count": skips,
                "gpt_challenges": challenges,
            }
        except Exception as e:
            return {"error": str(e)}

    def get_analytics_windows(self) -> list:
        """Performance breakdown by trading window."""
        try:
            cursor = self.db._conn.execute(
                "SELECT * FROM window_performance ORDER BY date DESC LIMIT 30"
            )
            return [dict(row) for row in cursor.fetchall()]
        except Exception:
            return []

    def get_analytics_daily(self, days: int = 30) -> list:
        """Daily P&L history."""
        try:
            cursor = self.db._conn.execute(
                """SELECT DATE(timestamp_close) as date,
                          COUNT(*) as trades,
                          SUM(CASE WHEN profit_usd > 0 THEN 1 ELSE 0 END) as wins,
                          SUM(CASE WHEN profit_usd < 0 THEN 1 ELSE 0 END) as losses,
                          COALESCE(SUM(profit_usd), 0) as pnl
                   FROM agent_trades
                   WHERE timestamp_close IS NOT NULL
                   GROUP BY DATE(timestamp_close)
                   ORDER BY date DESC
                   LIMIT ?""",
                (days,)
            )
            return [dict(row) for row in cursor.fetchall()]
        except Exception:
            return []

    def get_analytics_grades(self) -> dict:
        """A+/B/SKIP breakdown with execution rates."""
        try:
            conn = self.db._conn
            result = {}
            for grade in ["A+", "B", "SKIP"]:
                total = conn.execute(
                    "SELECT COUNT(*) FROM agent_decisions WHERE grade = ?", (grade,)
                ).fetchone()[0]
                executed = conn.execute(
                    "SELECT COUNT(*) FROM agent_decisions WHERE grade = ? AND executed = 1", (grade,)
                ).fetchone()[0]
                avg_conf = conn.execute(
                    "SELECT COALESCE(AVG(confidence), 0) FROM agent_decisions WHERE grade = ?", (grade,)
                ).fetchone()[0]
                result[grade] = {
                    "total": total,
                    "executed": executed,
                    "execution_rate": round(executed / total * 100, 1) if total > 0 else 0,
                    "avg_confidence": round(avg_conf, 1),
                }
            return result
        except Exception as e:
            return {"error": str(e)}
