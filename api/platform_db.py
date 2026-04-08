"""
ApexGold Platform — Platform Database
Handles users, applications, invites, and broadcasts.
Separate from agent trading data but same SQLite file.
"""

from __future__ import annotations

import sqlite3
import secrets
from datetime import datetime
from pathlib import Path
from typing import Optional
import os


class PlatformDB:
    """Manages platform tables: users, applications, invites, broadcasts."""

    def __init__(self) -> None:
        db_path = os.getenv("PLATFORM_DB_PATH", "agent/data/apexgold.db")
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_tables()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _row_to_dict(self, row: Optional[sqlite3.Row]) -> Optional[dict]:
        if row is None:
            return None
        return dict(row)

    def _rows_to_list(self, rows: list) -> list[dict]:
        return [dict(r) for r in rows]

    def _init_tables(self) -> None:
        try:
            with self._connect() as conn:
                conn.executescript("""
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        email TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        role TEXT NOT NULL DEFAULT 'mentee',
                        status TEXT NOT NULL DEFAULT 'active',
                        telegram_chat_id TEXT,
                        invite_code TEXT,
                        created_at TEXT NOT NULL,
                        last_login TEXT
                    );

                    CREATE TABLE IF NOT EXISTS applications (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        email TEXT UNIQUE NOT NULL,
                        country TEXT NOT NULL,
                        experience TEXT NOT NULL,
                        reason TEXT NOT NULL,
                        status TEXT NOT NULL DEFAULT 'pending',
                        created_at TEXT NOT NULL,
                        reviewed_at TEXT
                    );

                    CREATE TABLE IF NOT EXISTS invites (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        code TEXT UNIQUE NOT NULL,
                        email TEXT,
                        role TEXT NOT NULL DEFAULT 'mentee',
                        used INTEGER NOT NULL DEFAULT 0,
                        used_by_email TEXT,
                        created_at TEXT NOT NULL,
                        expires_at TEXT
                    );

                    CREATE TABLE IF NOT EXISTS broadcasts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL,
                        message TEXT NOT NULL,
                        owner_note TEXT,
                        trade_context TEXT,
                        created_at TEXT NOT NULL
                    );
                """)
        except Exception as e:
            print(f"[PlatformDB] Error initialising tables: {e}")

    # ------------------------------------------------------------------
    # Users
    # ------------------------------------------------------------------

    def create_user(
        self,
        name: str,
        email: str,
        password_hash: str,
        role: str,
        invite_code: Optional[str] = None,
    ) -> int:
        """Insert a new user. Returns the new user id, or -1 on failure."""
        try:
            now = datetime.utcnow().isoformat()
            with self._connect() as conn:
                cur = conn.execute(
                    """
                    INSERT INTO users (name, email, password_hash, role, status, invite_code, created_at)
                    VALUES (?, ?, ?, ?, 'active', ?, ?)
                    """,
                    (name, email, password_hash, role, invite_code, now),
                )
                return cur.lastrowid  # type: ignore[return-value]
        except Exception as e:
            print(f"[PlatformDB] create_user error: {e}")
            return -1

    def get_user_by_email(self, email: str) -> Optional[dict]:
        try:
            with self._connect() as conn:
                row = conn.execute(
                    "SELECT * FROM users WHERE email = ?", (email,)
                ).fetchone()
                return self._row_to_dict(row)
        except Exception as e:
            print(f"[PlatformDB] get_user_by_email error: {e}")
            return None

    def get_user_by_id(self, user_id: int) -> Optional[dict]:
        try:
            with self._connect() as conn:
                row = conn.execute(
                    "SELECT * FROM users WHERE id = ?", (user_id,)
                ).fetchone()
                return self._row_to_dict(row)
        except Exception as e:
            print(f"[PlatformDB] get_user_by_id error: {e}")
            return None

    def update_user_last_login(self, user_id: int) -> bool:
        try:
            now = datetime.utcnow().isoformat()
            with self._connect() as conn:
                conn.execute(
                    "UPDATE users SET last_login = ? WHERE id = ?", (now, user_id)
                )
            return True
        except Exception as e:
            print(f"[PlatformDB] update_user_last_login error: {e}")
            return False

    def update_user(self, user_id: int, updates: dict) -> bool:
        """Update arbitrary columns on a user row."""
        if not updates:
            return True
        allowed = {"name", "email", "password_hash", "role", "status", "telegram_chat_id"}
        filtered = {k: v for k, v in updates.items() if k in allowed}
        if not filtered:
            return False
        try:
            set_clause = ", ".join(f"{k} = ?" for k in filtered)
            values = list(filtered.values()) + [user_id]
            with self._connect() as conn:
                conn.execute(
                    f"UPDATE users SET {set_clause} WHERE id = ?", values
                )
            return True
        except Exception as e:
            print(f"[PlatformDB] update_user error: {e}")
            return False

    def get_all_users(self) -> list[dict]:
        try:
            with self._connect() as conn:
                rows = conn.execute(
                    "SELECT * FROM users ORDER BY created_at DESC"
                ).fetchall()
                return self._rows_to_list(rows)
        except Exception as e:
            print(f"[PlatformDB] get_all_users error: {e}")
            return []

    def get_mentees(self) -> list[dict]:
        """Return users with role 'mentee' or 'trial'."""
        try:
            with self._connect() as conn:
                rows = conn.execute(
                    "SELECT * FROM users WHERE role IN ('mentee', 'trial') ORDER BY created_at DESC"
                ).fetchall()
                return self._rows_to_list(rows)
        except Exception as e:
            print(f"[PlatformDB] get_mentees error: {e}")
            return []

    # ------------------------------------------------------------------
    # Applications
    # ------------------------------------------------------------------

    def submit_application(
        self,
        name: str,
        email: str,
        country: str,
        experience: str,
        reason: str,
    ) -> int:
        """Insert a new application. Returns new id, or -1 on failure."""
        try:
            now = datetime.utcnow().isoformat()
            with self._connect() as conn:
                cur = conn.execute(
                    """
                    INSERT INTO applications (name, email, country, experience, reason, status, created_at)
                    VALUES (?, ?, ?, ?, ?, 'pending', ?)
                    """,
                    (name, email, country, experience, reason, now),
                )
                return cur.lastrowid  # type: ignore[return-value]
        except Exception as e:
            print(f"[PlatformDB] submit_application error: {e}")
            return -1

    def get_applications(self, status: Optional[str] = None) -> list[dict]:
        try:
            with self._connect() as conn:
                if status is None:
                    rows = conn.execute(
                        "SELECT * FROM applications ORDER BY created_at DESC"
                    ).fetchall()
                else:
                    rows = conn.execute(
                        "SELECT * FROM applications WHERE status = ? ORDER BY created_at DESC",
                        (status,),
                    ).fetchall()
                return self._rows_to_list(rows)
        except Exception as e:
            print(f"[PlatformDB] get_applications error: {e}")
            return []

    def get_application_by_email(self, email: str) -> Optional[dict]:
        try:
            with self._connect() as conn:
                row = conn.execute(
                    "SELECT * FROM applications WHERE email = ?", (email,)
                ).fetchone()
                return self._row_to_dict(row)
        except Exception as e:
            print(f"[PlatformDB] get_application_by_email error: {e}")
            return None

    def update_application_status(self, app_id: int, status: str) -> bool:
        try:
            now = datetime.utcnow().isoformat()
            with self._connect() as conn:
                conn.execute(
                    "UPDATE applications SET status = ?, reviewed_at = ? WHERE id = ?",
                    (status, now, app_id),
                )
            return True
        except Exception as e:
            print(f"[PlatformDB] update_application_status error: {e}")
            return False

    # ------------------------------------------------------------------
    # Invites
    # ------------------------------------------------------------------

    def create_invite(
        self,
        email: Optional[str] = None,
        role: str = "mentee",
    ) -> str:
        """Create an invite code and return it. Returns empty string on failure."""
        try:
            code = secrets.token_urlsafe(16)
            now = datetime.utcnow().isoformat()
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT INTO invites (code, email, role, used, created_at)
                    VALUES (?, ?, ?, 0, ?)
                    """,
                    (code, email, role, now),
                )
            return code
        except Exception as e:
            print(f"[PlatformDB] create_invite error: {e}")
            return ""

    def get_invite(self, code: str) -> Optional[dict]:
        try:
            with self._connect() as conn:
                row = conn.execute(
                    "SELECT * FROM invites WHERE code = ?", (code,)
                ).fetchone()
                return self._row_to_dict(row)
        except Exception as e:
            print(f"[PlatformDB] get_invite error: {e}")
            return None

    def mark_invite_used(self, code: str, used_by_email: str) -> bool:
        try:
            with self._connect() as conn:
                conn.execute(
                    "UPDATE invites SET used = 1, used_by_email = ? WHERE code = ?",
                    (used_by_email, code),
                )
            return True
        except Exception as e:
            print(f"[PlatformDB] mark_invite_used error: {e}")
            return False

    def get_all_invites(self) -> list[dict]:
        try:
            with self._connect() as conn:
                rows = conn.execute(
                    "SELECT * FROM invites ORDER BY created_at DESC"
                ).fetchall()
                return self._rows_to_list(rows)
        except Exception as e:
            print(f"[PlatformDB] get_all_invites error: {e}")
            return []

    # ------------------------------------------------------------------
    # Broadcasts
    # ------------------------------------------------------------------

    def create_broadcast(
        self,
        title: str,
        message: str,
        owner_note: Optional[str] = None,
        trade_context: Optional[str] = None,
    ) -> int:
        """Insert a broadcast. Returns new id, or -1 on failure."""
        try:
            now = datetime.utcnow().isoformat()
            with self._connect() as conn:
                cur = conn.execute(
                    """
                    INSERT INTO broadcasts (title, message, owner_note, trade_context, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (title, message, owner_note, trade_context, now),
                )
                return cur.lastrowid  # type: ignore[return-value]
        except Exception as e:
            print(f"[PlatformDB] create_broadcast error: {e}")
            return -1

    def get_broadcasts(self, limit: int = 20) -> list[dict]:
        try:
            with self._connect() as conn:
                rows = conn.execute(
                    "SELECT * FROM broadcasts ORDER BY created_at DESC LIMIT ?",
                    (limit,),
                ).fetchall()
                return self._rows_to_list(rows)
        except Exception as e:
            print(f"[PlatformDB] get_broadcasts error: {e}")
            return []

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def init_owner(self, name: str, email: str, password_hash: str) -> bool:
        """Create the owner account only if no users exist yet."""
        try:
            with self._connect() as conn:
                count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
                if count > 0:
                    return False
            user_id = self.create_user(name, email, password_hash, role="owner")
            return user_id != -1
        except Exception as e:
            print(f"[PlatformDB] init_owner error: {e}")
            return False

    def user_count(self) -> int:
        """Return total number of users."""
        try:
            with self._connect() as conn:
                return conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        except Exception as e:
            print(f"[PlatformDB] user_count error: {e}")
            return 0
