"""
GoldTrader AI Agent — Database
SQLite logging for all decisions, trades, window performance, and agent state.
Reference: ARCHITECTURE.md Section 4, Section 13 (concurrency)
"""

import sqlite3
import json
from datetime import datetime, date
from pathlib import Path
from typing import Optional


class Database:
    """
    SQLite database for agent state persistence.
    Uses WAL mode for safe concurrent access from main loop + TP1 monitor thread.
    """

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: Optional[sqlite3.Connection] = None
        self._connect()
        self._create_tables()

    def _connect(self):
        """Open connection with WAL mode and thread safety."""
        self._conn = sqlite3.connect(
            str(self.db_path),
            check_same_thread=False,
            timeout=10,
        )
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")

    def _create_tables(self):
        """Create all tables on first run. Schema from ARCHITECTURE.md Section 4."""
        self._conn.executescript("""
            -- Every agent decision regardless of outcome
            CREATE TABLE IF NOT EXISTS agent_decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                window_name TEXT,
                grade TEXT,
                direction TEXT,
                entry_price REAL,
                entry_zone TEXT,
                sl_level REAL,
                tp1_level REAL,
                tp2_level REAL,
                invalidation TEXT,
                reasoning TEXT,
                confidence INTEGER,
                pillar_trend TEXT,
                pillar_momentum TEXT,
                pillar_location TEXT,
                setup_type TEXT,
                base_zone TEXT,
                news_risk TEXT,
                news_summary TEXT,
                gpt_verdict TEXT,
                gpt_reasoning TEXT,
                executed BOOLEAN DEFAULT FALSE,
                skip_reason TEXT,
                execution_reason TEXT
            );

            -- Every trade placed by agent
            CREATE TABLE IF NOT EXISTS agent_trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id INTEGER UNIQUE,
                timestamp_open TEXT,
                timestamp_close TEXT,
                direction TEXT,
                lot_size REAL,
                entry_price REAL,
                sl_price REAL,
                tp1_price REAL,
                tp2_price REAL,
                exit_price REAL,
                profit_usd REAL,
                profit_pips REAL,
                exit_reason TEXT,
                account_type TEXT,
                decision_id INTEGER,
                FOREIGN KEY (decision_id) REFERENCES agent_decisions(id)
            );

            -- Performance aggregated by window
            CREATE TABLE IF NOT EXISTS window_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                window_name TEXT,
                trades_taken INTEGER DEFAULT 0,
                trades_won INTEGER DEFAULT 0,
                trades_lost INTEGER DEFAULT 0,
                total_pnl REAL DEFAULT 0,
                avg_confidence REAL,
                claude_a_plus INTEGER DEFAULT 0,
                gpt_challenges INTEGER DEFAULT 0,
                UNIQUE(date, window_name)
            );

            -- Session summaries for Claude context and Telegram digest
            CREATE TABLE IF NOT EXISTS session_summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                window_name TEXT NOT NULL,
                session_label TEXT,
                window_start TEXT,
                window_end TEXT,
                session_high REAL,
                session_low REAL,
                range_pts REAL,
                character TEXT,
                total_cycles INTEGER DEFAULT 0,
                prefilter_pass INTEGER DEFAULT 0,
                claude_called INTEGER DEFAULT 0,
                trades_taken INTEGER DEFAULT 0,
                session_pnl REAL DEFAULT 0.0,
                top_skip_reasons TEXT,
                h4_direction TEXT,
                notes TEXT,
                UNIQUE(date, window_name)
            );

            -- Agent state for dashboard
            CREATE TABLE IF NOT EXISTS agent_state (
                id INTEGER PRIMARY KEY,
                status TEXT,
                current_window TEXT,
                last_analysis_time TEXT,
                last_trade_time TEXT,
                daily_pnl REAL,
                updated_at TEXT
            );
        """)
        self._conn.commit()

        # Initialize agent_state row if not exists
        cursor = self._conn.execute("SELECT COUNT(*) FROM agent_state")
        if cursor.fetchone()[0] == 0:
            self._conn.execute(
                "INSERT INTO agent_state (id, status, updated_at) VALUES (1, 'starting', ?)",
                (datetime.utcnow().isoformat(),)
            )
            self._conn.commit()

    # ------------------------------------------------------------------
    # Decisions
    # ------------------------------------------------------------------

    def log_decision(self, decision: dict) -> int:
        """Log an agent decision. Returns decision_id."""
        try:
            fields = [
                "timestamp", "window_name", "grade", "direction",
                "entry_price", "entry_zone", "sl_level", "tp1_level", "tp2_level",
                "invalidation", "reasoning", "confidence",
                "pillar_trend", "pillar_momentum", "pillar_location",
                "setup_type", "base_zone",
                "news_risk", "news_summary",
                "gpt_verdict", "gpt_reasoning",
                "executed", "skip_reason", "execution_reason",
            ]
            # Default timestamp if not provided
            if "timestamp" not in decision:
                decision["timestamp"] = datetime.utcnow().isoformat()

            values = [decision.get(f) for f in fields]
            placeholders = ", ".join(["?"] * len(fields))
            columns = ", ".join(fields)

            cursor = self._conn.execute(
                f"INSERT INTO agent_decisions ({columns}) VALUES ({placeholders})",
                values
            )
            self._conn.commit()
            return cursor.lastrowid
        except Exception as e:
            print(f"ERROR | database | log_decision failed: {e}")
            return -1

    def get_recent_decisions(self, n: int = 5) -> list:
        """Get last N decisions, newest first."""
        try:
            cursor = self._conn.execute(
                "SELECT * FROM agent_decisions ORDER BY id DESC LIMIT ?", (n,)
            )
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"ERROR | database | get_recent_decisions failed: {e}")
            return []

    # ------------------------------------------------------------------
    # Trades
    # ------------------------------------------------------------------

    def log_trade(self, trade: dict) -> int:
        """Log a trade placement. Returns trade_id."""
        try:
            fields = [
                "ticket_id", "timestamp_open", "direction",
                "lot_size", "entry_price", "sl_price", "tp1_price", "tp2_price",
                "account_type", "decision_id",
            ]
            if "timestamp_open" not in trade:
                trade["timestamp_open"] = datetime.utcnow().isoformat()

            values = [trade.get(f) for f in fields]
            placeholders = ", ".join(["?"] * len(fields))
            columns = ", ".join(fields)

            cursor = self._conn.execute(
                f"INSERT INTO agent_trades ({columns}) VALUES ({placeholders})",
                values
            )
            self._conn.commit()
            return cursor.lastrowid
        except Exception as e:
            print(f"ERROR | database | log_trade failed: {e}")
            return -1

    def update_trade(self, ticket_id: int, update: dict) -> bool:
        """Update a trade record by ticket_id."""
        try:
            sets = ", ".join([f"{k} = ?" for k in update.keys()])
            values = list(update.values()) + [ticket_id]
            self._conn.execute(
                f"UPDATE agent_trades SET {sets} WHERE ticket_id = ?",
                values
            )
            self._conn.commit()
            return True
        except Exception as e:
            print(f"ERROR | database | update_trade failed: {e}")
            return False

    def get_recent_trades(self, n: int = 3) -> list:
        """Get last N trades, newest first."""
        try:
            cursor = self._conn.execute(
                "SELECT * FROM agent_trades ORDER BY id DESC LIMIT ?", (n,)
            )
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"ERROR | database | get_recent_trades failed: {e}")
            return []

    def get_last_trade_time(self) -> Optional[str]:
        """Get timestamp of most recent trade (open or close)."""
        try:
            cursor = self._conn.execute(
                """SELECT COALESCE(timestamp_close, timestamp_open)
                   FROM agent_trades ORDER BY id DESC LIMIT 1"""
            )
            row = cursor.fetchone()
            return row[0] if row else None
        except Exception:
            return None

    def get_last_trade_was_loss(self) -> bool:
        """Check if the most recent closed trade was a loss."""
        try:
            cursor = self._conn.execute(
                """SELECT profit_usd FROM agent_trades
                   WHERE timestamp_close IS NOT NULL
                   ORDER BY id DESC LIMIT 1"""
            )
            row = cursor.fetchone()
            if row and row[0] is not None:
                return row[0] < 0
            return False
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Daily P&L
    # ------------------------------------------------------------------

    def get_daily_pnl(self) -> float:
        """Sum of today's closed trade P&L."""
        try:
            today = date.today().isoformat()
            cursor = self._conn.execute(
                """SELECT COALESCE(SUM(profit_usd), 0.0) FROM agent_trades
                   WHERE timestamp_close IS NOT NULL
                   AND DATE(timestamp_close) = ?""",
                (today,)
            )
            return cursor.fetchone()[0]
        except Exception as e:
            print(f"ERROR | database | get_daily_pnl failed: {e}")
            return 0.0

    # ------------------------------------------------------------------
    # Positions count (from database records)
    # ------------------------------------------------------------------

    def get_open_positions_count(self) -> int:
        """Count trades that are open (no close timestamp)."""
        try:
            cursor = self._conn.execute(
                "SELECT COUNT(*) FROM agent_trades WHERE timestamp_close IS NULL"
            )
            return cursor.fetchone()[0]
        except Exception as e:
            print(f"ERROR | database | get_open_positions_count failed: {e}")
            return 0

    # ------------------------------------------------------------------
    # Agent State
    # ------------------------------------------------------------------

    def update_agent_state(self, state: dict) -> bool:
        """Update the single agent_state row."""
        try:
            state["updated_at"] = datetime.utcnow().isoformat()
            sets = ", ".join([f"{k} = ?" for k in state.keys()])
            values = list(state.values())
            self._conn.execute(
                f"UPDATE agent_state SET {sets} WHERE id = 1",
                values
            )
            self._conn.commit()
            return True
        except Exception as e:
            print(f"ERROR | database | update_agent_state failed: {e}")
            return False

    def get_agent_state(self) -> dict:
        """Get current agent state."""
        try:
            cursor = self._conn.execute("SELECT * FROM agent_state WHERE id = 1")
            row = cursor.fetchone()
            return dict(row) if row else {}
        except Exception:
            return {}

    # ------------------------------------------------------------------
    # Window Performance
    # ------------------------------------------------------------------

    def update_window_performance(self, date_str: str, window: str, data: dict) -> bool:
        """Upsert window performance for a given date and window."""
        try:
            # Try insert first
            existing = self._conn.execute(
                "SELECT id FROM window_performance WHERE date = ? AND window_name = ?",
                (date_str, window)
            ).fetchone()

            if existing:
                sets = ", ".join([f"{k} = ?" for k in data.keys()])
                values = list(data.values()) + [date_str, window]
                self._conn.execute(
                    f"UPDATE window_performance SET {sets} WHERE date = ? AND window_name = ?",
                    values
                )
            else:
                data["date"] = date_str
                data["window_name"] = window
                columns = ", ".join(data.keys())
                placeholders = ", ".join(["?"] * len(data))
                self._conn.execute(
                    f"INSERT INTO window_performance ({columns}) VALUES ({placeholders})",
                    list(data.values())
                )

            self._conn.commit()
            return True
        except Exception as e:
            print(f"ERROR | database | update_window_performance failed: {e}")
            return False

    # ------------------------------------------------------------------
    # Session Summaries
    # ------------------------------------------------------------------

    def save_session_summary(self, summary: dict) -> bool:
        """Upsert a session summary at window close."""
        try:
            fields = [
                "date", "window_name", "session_label",
                "window_start", "window_end",
                "session_high", "session_low", "range_pts", "character",
                "total_cycles", "prefilter_pass", "claude_called",
                "trades_taken", "session_pnl",
                "top_skip_reasons", "h4_direction", "notes",
            ]
            existing = self._conn.execute(
                "SELECT id FROM session_summaries WHERE date = ? AND window_name = ?",
                (summary.get("date"), summary.get("window_name"))
            ).fetchone()

            if existing:
                sets = ", ".join([f"{f} = ?" for f in fields])
                values = [summary.get(f) for f in fields]
                values += [summary.get("date"), summary.get("window_name")]
                self._conn.execute(
                    f"UPDATE session_summaries SET {sets} "
                    f"WHERE date = ? AND window_name = ?",
                    values
                )
            else:
                columns = ", ".join(fields)
                placeholders = ", ".join(["?"] * len(fields))
                values = [summary.get(f) for f in fields]
                self._conn.execute(
                    f"INSERT INTO session_summaries ({columns}) VALUES ({placeholders})",
                    values
                )
            self._conn.commit()
            return True
        except Exception as e:
            print(f"ERROR | database | save_session_summary failed: {e}")
            return False

    def get_recent_session_summaries(self, n: int = 3) -> list:
        """Get last N session summaries, newest first."""
        try:
            cursor = self._conn.execute(
                """SELECT * FROM session_summaries
                   ORDER BY date DESC, id DESC LIMIT ?""",
                (n,)
            )
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"ERROR | database | get_recent_session_summaries failed: {e}")
            return []

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def close(self):
        """Close database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None
