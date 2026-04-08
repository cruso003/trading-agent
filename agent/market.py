"""
GoldTrader AI Agent — Market Data
MT5 connection, candle fetching, account info, and economic calendar.
Reference: ARCHITECTURE.md Section 3, mt5-bot/src for patterns
"""

import logging
import time
from datetime import datetime, timezone, timedelta
from typing import Optional

logger = logging.getLogger("market")

# Default symbol — overridden by config.symbol at runtime
DEFAULT_SYMBOL = "XAUUSDm"

# MT5 timeframe constants (will be imported from MetaTrader5 at runtime)
# Defined here as fallback values matching MT5 constants
TF_M15 = 15
TF_M30 = 30
TF_H1 = 60
TF_H4 = 240

# Map string names to MT5 timeframe constants
TIMEFRAME_MAP = {
    "M15": TF_M15,
    "M30": TF_M30,
    "H1": TF_H1,
    "H4": TF_H4,
}


class Market:
    """
    MT5 market data interface.
    All MT5 operations are wrapped in try/except.
    MetaTrader5 module imported lazily (only available on Windows).
    """

    def __init__(self):
        self._mt5 = None
        self._connected = False

    def _import_mt5(self):
        """Lazy import of MetaTrader5 (only available on Windows)."""
        if self._mt5 is None:
            try:
                import MetaTrader5 as mt5
                self._mt5 = mt5
                # Update timeframe constants from actual module
                global TF_M15, TF_M30, TF_H1, TF_H4, TIMEFRAME_MAP
                TF_M15 = mt5.TIMEFRAME_M15
                TF_M30 = mt5.TIMEFRAME_M30
                TF_H1 = mt5.TIMEFRAME_H1
                TF_H4 = mt5.TIMEFRAME_H4
                TIMEFRAME_MAP = {
                    "M15": TF_M15, "M30": TF_M30,
                    "H1": TF_H1, "H4": TF_H4,
                }
            except ImportError:
                logger.error("MetaTrader5 not available (Windows only)")
                raise
        return self._mt5

    def connect(self, login: str = "", password: str = "", server: str = "") -> bool:
        """
        Initialize MT5 and log in.
        Reference: mt5-bot connection patterns
        """
        try:
            mt5 = self._import_mt5()

            # Ensure clean state before connecting (mt5-bot pattern)
            mt5.shutdown()

            if not mt5.initialize():
                logger.error(f"MT5 initialize failed: {mt5.last_error()}")
                return False

            if login and password and server:
                authorized = mt5.login(
                    int(login),
                    password=password,
                    server=server,
                )
                if not authorized:
                    logger.error(f"MT5 login failed: {mt5.last_error()}")
                    mt5.shutdown()
                    return False

            self._connected = True
            logger.info("MT5 connected successfully")
            return True

        except Exception as e:
            logger.error(f"MT5 connect exception: {e}")
            return False

    def disconnect(self) -> None:
        """Shutdown MT5 connection."""
        try:
            if self._mt5 and self._connected:
                self._mt5.shutdown()
                self._connected = False
                logger.info("MT5 disconnected")
        except Exception as e:
            logger.warning(f"MT5 disconnect error: {e}")

    def is_connected(self) -> bool:
        """Check if MT5 is connected and responsive."""
        if not self._connected or not self._mt5:
            return False
        try:
            info = self._mt5.terminal_info()
            return info is not None
        except Exception:
            self._connected = False
            return False

    def get_candles(self, symbol: str = DEFAULT_SYMBOL, timeframe: str = "M15", count: int = 100) -> list:
        """
        Fetch OHLCV candles from MT5.
        Returns list of dicts with: time, open, high, low, close, volume
        """
        try:
            mt5 = self._import_mt5()
            tf = TIMEFRAME_MAP.get(timeframe, TF_M15)

            rates = mt5.copy_rates_from_pos(symbol, tf, 0, count)
            if rates is None or len(rates) == 0:
                logger.warning(f"No candles returned for {symbol} {timeframe}")
                return []

            candles = []
            for r in rates:
                candles.append({
                    "time": datetime.fromtimestamp(r[0], tz=timezone.utc).isoformat(),
                    "open": float(r[1]),
                    "high": float(r[2]),
                    "low": float(r[3]),
                    "close": float(r[4]),
                    "volume": int(r[5]),
                })
            return candles

        except Exception as e:
            logger.error(f"get_candles failed: {e}")
            return []

    def get_current_price(self, symbol: str = DEFAULT_SYMBOL) -> dict:
        """Get current bid/ask/spread."""
        try:
            mt5 = self._import_mt5()
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                logger.warning(f"No tick data for {symbol}")
                return {}

            return {
                "bid": tick.bid,
                "ask": tick.ask,
                "spread": round(tick.ask - tick.bid, 2),
                "time": datetime.fromtimestamp(tick.time, tz=timezone.utc).isoformat(),
            }
        except Exception as e:
            logger.error(f"get_current_price failed: {e}")
            return {}

    def get_account_info(self) -> dict:
        """
        Get account balance info.
        Returns balance as number only, no label (AI isolation principle).
        """
        try:
            mt5 = self._import_mt5()
            info = mt5.account_info()
            if info is None:
                logger.warning("No account info returned")
                return {}

            return {
                "balance": info.balance,
                "equity": info.equity,
                "margin_free": info.margin_free,
                "profit": info.profit,
            }
        except Exception as e:
            logger.error(f"get_account_info failed: {e}")
            return {}

    def get_open_positions(self, symbol: str = DEFAULT_SYMBOL, magic: int = 234001) -> list:
        """Get all open positions with our magic number."""
        try:
            mt5 = self._import_mt5()
            positions = mt5.positions_get(symbol=symbol)
            if positions is None:
                return []

            result = []
            for pos in positions:
                if pos.magic == magic:
                    result.append({
                        "ticket": pos.ticket,
                        "direction": "BUY" if pos.type == 0 else "SELL",
                        "volume": pos.volume,
                        "open_price": pos.price_open,
                        "sl": pos.sl,
                        "tp": pos.tp,
                        "profit": pos.profit,
                        "magic": pos.magic,
                        "time": datetime.fromtimestamp(pos.time, tz=timezone.utc).isoformat(),
                    })
            return result

        except Exception as e:
            logger.error(f"get_open_positions failed: {e}")
            return []

    def get_economic_calendar(self, hours_ahead: int = 1) -> list:
        """
        Check MT5 economic calendar for HIGH impact events.
        Returns list of upcoming events within the specified window.
        """
        try:
            mt5 = self._import_mt5()
            now = datetime.now(timezone.utc)
            future = now + timedelta(hours=hours_ahead)

            # Note: MT5 Python API calendar support varies by build.
            # If calendar_get is not available, return empty (news.py
            # will fall through to Perplexity if ATR anomaly detected).
            if hasattr(mt5, 'calendar_get'):
                cal_events = mt5.calendar_get(now, future)
                if cal_events is None:
                    return []

                high_impact = []
                for evt in cal_events:
                    if hasattr(evt, 'importance') and evt.importance >= 2:
                        high_impact.append({
                            "name": getattr(evt, 'event_name', 'Unknown'),
                            "time": getattr(evt, 'time', ''),
                            "impact": "HIGH" if evt.importance >= 3 else "MEDIUM",
                            "currency": getattr(evt, 'currency', ''),
                        })
                return high_impact

            return []

        except Exception as e:
            logger.warning(f"get_economic_calendar failed: {e}")
            return []

    def wait_for_next_m15(self, stop_check=None) -> None:
        """
        Block until the next M15 candle closes.
        Calculates remaining seconds to next 15-minute boundary.
        stop_check: optional callable — if it returns True, exits early (for graceful shutdown).
        """
        now = datetime.now(timezone.utc)
        current_minute = now.minute
        current_second = now.second

        # Next M15 boundary: 0, 15, 30, 45
        next_m15 = ((current_minute // 15) + 1) * 15
        if next_m15 >= 60:
            minutes_to_wait = 60 - current_minute
        else:
            minutes_to_wait = next_m15 - current_minute

        seconds_to_wait = (minutes_to_wait * 60) - current_second + 2  # +2s buffer
        if seconds_to_wait <= 0:
            seconds_to_wait = 1

        logger.debug(f"Waiting {seconds_to_wait}s for next M15 close")
        for _ in range(seconds_to_wait):
            if stop_check and stop_check():
                logger.debug("Wait interrupted by shutdown signal")
                return
            time.sleep(1)
