"""
GoldTrader AI Agent — Configuration
Loads all .env variables, validates required keys, exposes typed settings.
Reference: ARCHITECTURE.md Section 9
"""

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root (one level above agent/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


def _require(key: str) -> str:
    """Get required env var or exit immediately."""
    value = os.getenv(key)
    if not value:
        print(f"FATAL: Missing required environment variable: {key}")
        print(f"       Copy .env.example to .env and fill in values.")
        sys.exit(1)
    return value


def _get(key: str, default: str = "") -> str:
    """Get optional env var with default."""
    return os.getenv(key, default)


def _get_float(key: str, default: float) -> float:
    """Get float env var with default."""
    raw = os.getenv(key)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError:
        print(f"WARNING: Invalid float for {key}={raw}, using default {default}")
        return default


def _get_int(key: str, default: int) -> int:
    """Get int env var with default."""
    raw = os.getenv(key)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        print(f"WARNING: Invalid int for {key}={raw}, using default {default}")
        return default


@dataclass(frozen=True)
class Config:
    """Immutable configuration loaded once at startup."""

    # --- AI APIs ---
    anthropic_api_key: str
    openai_api_key: str
    perplexity_api_key: str

    # --- Telegram ---
    telegram_bot_token: str
    telegram_chat_id: str

    # --- MT5 Demo ---
    mt5_demo_login: str
    mt5_demo_password: str
    mt5_demo_server: str

    # --- MT5 Live ---
    mt5_live_login: str
    mt5_live_password: str
    mt5_live_server: str

    # --- Active Account ---
    active_account: str  # "demo" or "live"

    # --- Risk Parameters ---
    max_daily_loss_usd: float
    max_positions: int
    max_risk_per_trade: float
    sl_min_points: int
    sl_max_points: int
    min_rr_ratio: float
    post_trade_cooling_minutes: int
    post_loss_cooling_minutes: int

    # --- Trading Windows (GMT+0) ---
    window_1_start: str
    window_1_end: str
    window_2_start: str
    window_2_end: str

    # --- Models ---
    claude_model: str
    gpt_model: str

    # --- Runtime ---
    log_level: str
    db_path: str
    news_cache_minutes: int

    # --- Derived ---
    project_root: Path

    @property
    def mt5_login(self) -> str:
        """Return login for the active account."""
        if self.active_account == "live":
            return self.mt5_live_login
        return self.mt5_demo_login

    @property
    def mt5_password(self) -> str:
        """Return password for the active account."""
        if self.active_account == "live":
            return self.mt5_live_password
        return self.mt5_demo_password

    @property
    def mt5_server(self) -> str:
        """Return server for the active account."""
        if self.active_account == "live":
            return self.mt5_live_server
        return self.mt5_demo_server

    @property
    def db_full_path(self) -> Path:
        """Absolute path to database file."""
        return self.project_root / self.db_path

    @property
    def playbook_path(self) -> Path:
        """Absolute path to PLAYBOOK.md (Claude system prompt)."""
        return self.project_root / "PLAYBOOK.md"


def load_config() -> Config:
    """
    Load and validate all configuration from environment.
    Fails loudly on missing required keys.
    Called once at startup.
    """
    # Validate active account value
    active = _get("ACTIVE_ACCOUNT", "demo").lower()
    if active not in ("demo", "live"):
        print(f"FATAL: ACTIVE_ACCOUNT must be 'demo' or 'live', got '{active}'")
        sys.exit(1)

    # Build DB path: resolve relative to project root
    db_path = _get("DB_PATH", "agent/data/agent.db")

    config = Config(
        # AI APIs
        anthropic_api_key=_require("ANTHROPIC_API_KEY"),
        openai_api_key=_require("OPENAI_API_KEY"),
        perplexity_api_key=_require("PERPLEXITY_API_KEY"),

        # Telegram
        telegram_bot_token=_require("TELEGRAM_BOT_TOKEN"),
        telegram_chat_id=_require("TELEGRAM_CHAT_ID"),

        # MT5 Demo
        mt5_demo_login=_require("MT5_DEMO_LOGIN"),
        mt5_demo_password=_require("MT5_DEMO_PASSWORD"),
        mt5_demo_server=_require("MT5_DEMO_SERVER"),

        # MT5 Live — required in .env but may be empty if only using demo
        mt5_live_login=_get("MT5_LIVE_LOGIN", ""),
        mt5_live_password=_get("MT5_LIVE_PASSWORD", ""),
        mt5_live_server=_get("MT5_LIVE_SERVER", ""),

        # Active Account
        active_account=active,

        # Risk Parameters
        max_daily_loss_usd=_get_float("MAX_DAILY_LOSS_USD", 50.0),
        max_positions=_get_int("MAX_POSITIONS", 2),
        max_risk_per_trade=_get_float("MAX_RISK_PER_TRADE", 0.02),
        sl_min_points=_get_int("SL_MIN_POINTS", 8),
        sl_max_points=_get_int("SL_MAX_POINTS", 50),
        min_rr_ratio=_get_float("MIN_RR_RATIO", 1.5),
        post_trade_cooling_minutes=_get_int("POST_TRADE_COOLING_MINUTES", 20),
        post_loss_cooling_minutes=_get_int("POST_LOSS_COOLING_MINUTES", 30),

        # Trading Windows
        window_1_start=_get("WINDOW_1_START", "23:00"),
        window_1_end=_get("WINDOW_1_END", "01:00"),
        window_2_start=_get("WINDOW_2_START", "12:00"),
        window_2_end=_get("WINDOW_2_END", "14:00"),

        # Models
        claude_model=_get("CLAUDE_MODEL", "claude-sonnet-4-6"),
        gpt_model=_get("GPT_MODEL", "gpt-4o"),

        # Runtime
        log_level=_get("LOG_LEVEL", "INFO").upper(),
        db_path=db_path,
        news_cache_minutes=_get_int("NEWS_CACHE_MINUTES", 15),

        # Derived
        project_root=PROJECT_ROOT,
    )

    # Validate live credentials if active_account is live
    if config.active_account == "live":
        if not config.mt5_live_login or not config.mt5_live_password:
            print("FATAL: ACTIVE_ACCOUNT=live but MT5_LIVE_LOGIN or MT5_LIVE_PASSWORD missing")
            sys.exit(1)

    return config
