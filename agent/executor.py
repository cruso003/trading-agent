"""
GoldTrader AI Agent — Trade Executor
MT5 order placement, position management, and trade monitoring.
Reference: ARCHITECTURE.md Section 8, Section 13 (concurrency), mt5-bot/src

Monitor behaviour (PLAYBOOK v2.0 Trade Management):
  Phase 1 — entry → +10pt: SL stays at original structural level
  Phase 2 — +10pt → TP1: SL moves to breakeven (locks 0-loss)
  Phase 3 — TP1 hit: close 50%, SL already at BE
  Phase 4 — 90min elapsed: force-close remaining position
"""

import logging
import threading
import time
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger("executor")

# Trade management thresholds (points, 1 point = $0.01 on XAUUSD)
BE_TRIGGER_POINTS = 10.0       # Move SL to BE after +10pt favourable
TIME_STOP_MINUTES = 90         # Force-close after 90 minutes
MONITOR_INTERVAL_SECONDS = 30


class Executor:
    """
    MT5 trade execution and position management.
    TP1 monitoring runs in a daemon background thread.
    Reference: ARCHITECTURE.md Section 13
    """

    def __init__(self, market, db, notifier, config):
        """
        Args:
            market: Market instance (for MT5 operations)
            db: Database instance
            notifier: Notifier instance
            config: Config instance
        """
        self.market = market
        self.db = db
        self.notifier = notifier
        self.config = config
        self.symbol = config.symbol
        self.magic = config.magic_number
        self._monitor_threads = {}  # ticket_id -> thread

    def place_trade(
        self,
        direction: str,
        lot_size: float,
        sl: float,
        tp1: float,
        tp2: float,
        comment: str = "",
    ) -> tuple:
        """
        Place a market order on MT5.
        Returns: (success: bool, ticket_id: int, error_msg: str)

        Magic number: 234001 always.
        Verifies order after placement.
        """
        try:
            mt5 = self.market._import_mt5()

            # Get current price
            price_info = self.market.get_current_price()
            if not price_info:
                return (False, 0, "Cannot get current price")

            # Determine order type and price
            if direction == "BUY":
                order_type = mt5.ORDER_TYPE_BUY
                price = price_info["ask"]
            elif direction == "SELL":
                order_type = mt5.ORDER_TYPE_SELL
                price = price_info["bid"]
            else:
                return (False, 0, f"Invalid direction: {direction}")

            # Use TP2 as the MT5 take profit (TP1 managed by monitor thread)
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": self.symbol,
                "volume": lot_size,
                "type": order_type,
                "price": price,
                "sl": sl,
                "tp": tp2,
                "deviation": 20,
                "magic": self.magic,
                "comment": comment[:31] if comment else "GoldTrader",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }

            # Send order
            result = mt5.order_send(request)

            if result is None:
                error = mt5.last_error()
                logger.error(f"order_send returned None: {error}")
                return (False, 0, f"MT5 error: {error}")

            if result.retcode != mt5.TRADE_RETCODE_DONE:
                logger.error(f"Order failed: retcode={result.retcode}, comment={result.comment}")
                return (False, 0, f"MT5 retcode {result.retcode}: {result.comment}")

            ticket_id = result.order
            logger.info(
                f"PLACED | ticket={ticket_id}, {direction} {lot_size} lots @ {price}, "
                f"SL={sl}, TP2={tp2}"
            )

            # Verify placement
            verified = self._verify_order(ticket_id)
            if not verified:
                logger.warning(f"Order {ticket_id} placed but verification failed")

            # Start TP1 monitoring thread
            self._start_tp1_monitor(ticket_id, tp1, price, direction)

            return (True, ticket_id, "")

        except Exception as e:
            logger.error(f"place_trade exception: {e}")
            return (False, 0, str(e))

    def close_trade(self, ticket_id: int) -> bool:
        """Close an open position by ticket ID."""
        try:
            mt5 = self.market._import_mt5()

            position = self._get_mt5_position(ticket_id)
            if position is None:
                logger.warning(f"Position {ticket_id} not found for close")
                return False

            # Reverse direction to close
            if position.type == 0:  # BUY
                close_type = mt5.ORDER_TYPE_SELL
                price = self.market.get_current_price().get("bid", 0)
            else:  # SELL
                close_type = mt5.ORDER_TYPE_BUY
                price = self.market.get_current_price().get("ask", 0)

            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": self.symbol,
                "volume": position.volume,
                "type": close_type,
                "position": ticket_id,
                "price": price,
                "deviation": 20,
                "magic": self.magic,
                "comment": "GoldTrader close",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }

            result = mt5.order_send(request)
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                logger.info(f"CLOSED | ticket={ticket_id}")
                return True

            logger.error(f"Close failed for {ticket_id}: {result}")
            return False

        except Exception as e:
            logger.error(f"close_trade exception: {e}")
            return False

    def close_partial(self, ticket_id: int, volume: float) -> bool:
        """Close part of a position (for TP1 management)."""
        try:
            mt5 = self.market._import_mt5()

            position = self._get_mt5_position(ticket_id)
            if position is None:
                return False

            if position.type == 0:  # BUY
                close_type = mt5.ORDER_TYPE_SELL
                price = self.market.get_current_price().get("bid", 0)
            else:  # SELL
                close_type = mt5.ORDER_TYPE_BUY
                price = self.market.get_current_price().get("ask", 0)

            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": self.symbol,
                "volume": round(volume, 2),
                "type": close_type,
                "position": ticket_id,
                "price": price,
                "deviation": 10,
                "magic": self.magic,
                "comment": "GoldTrader TP1",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }

            result = mt5.order_send(request)
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                logger.info(f"PARTIAL CLOSE | ticket={ticket_id}, volume={volume}")
                return True

            logger.error(f"Partial close failed for {ticket_id}: {result}")
            return False

        except Exception as e:
            logger.error(f"close_partial exception: {e}")
            return False

    def modify_sl(self, ticket_id: int, new_sl: float) -> bool:
        """Modify stop loss of an open position."""
        try:
            mt5 = self.market._import_mt5()

            position = self._get_mt5_position(ticket_id)
            if position is None:
                return False

            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "symbol": self.symbol,
                "position": ticket_id,
                "sl": new_sl,
                "tp": position.tp,
                "magic": self.magic,
            }

            result = mt5.order_send(request)
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                logger.info(f"SL MODIFIED | ticket={ticket_id}, new_sl={new_sl}")
                return True

            logger.error(f"SL modify failed for {ticket_id}: {result}")
            return False

        except Exception as e:
            logger.error(f"modify_sl exception: {e}")
            return False

    def get_position(self, ticket_id: int) -> Optional[dict]:
        """Get position info as dict."""
        pos = self._get_mt5_position(ticket_id)
        if pos is None:
            return None
        return {
            "ticket": pos.ticket,
            "direction": "BUY" if pos.type == 0 else "SELL",
            "volume": pos.volume,
            "open_price": pos.price_open,
            "current_price": pos.price_current,
            "sl": pos.sl,
            "tp": pos.tp,
            "profit": pos.profit,
        }

    def check_positions(self) -> list:
        """Get all open positions with our magic number."""
        return self.market.get_open_positions(magic=self.magic)

    # ------------------------------------------------------------------
    # TP1 Monitoring (background daemon thread)
    # Reference: ARCHITECTURE.md Section 13
    # ------------------------------------------------------------------

    def _start_tp1_monitor(self, ticket_id: int, tp1_level: float, entry_price: float, direction: str):
        """Start a daemon thread to monitor TP1 for a position."""
        if ticket_id in self._monitor_threads:
            logger.warning(f"TP1 monitor already running for {ticket_id}")
            return

        thread = threading.Thread(
            target=self._tp1_monitor_loop,
            args=(ticket_id, tp1_level, entry_price, direction),
            daemon=True,
            name=f"tp1_monitor_{ticket_id}",
        )
        self._monitor_threads[ticket_id] = thread
        thread.start()
        logger.info(f"TP1 monitor started for ticket {ticket_id}, target={tp1_level}")

    def _tp1_monitor_loop(self, ticket_id: int, tp1_level: float, entry_price: float, direction: str):
        """
        Background loop: poll every 30s. Implements PLAYBOOK v2.0 Phases 2-4.

        Events handled (each triggers once, then flag stays set):
          BE: when favourable excursion >= BE_TRIGGER_POINTS → move SL to
              entry price. Protects capital early on slow-mover scalps.
          TP1: when price reaches tp1_level → close 50%, ensure SL at BE,
               notify Telegram.
          TIME_STOP: when open for TIME_STOP_MINUTES → force-close the
                     remainder. Quick scalps do not hold for hours.
        Thread exits when position closes or time stop fires.
        """
        be_moved = False
        tp1_hit = False
        started_at = time.monotonic()

        try:
            while True:
                time.sleep(MONITOR_INTERVAL_SECONDS)

                pos = self._get_mt5_position(ticket_id)
                if pos is None:
                    logger.info(
                        f"Monitor: position {ticket_id} closed externally, exiting"
                    )
                    break

                current_price = pos.price_current
                elapsed_minutes = (time.monotonic() - started_at) / 60.0

                # Favourable-points excursion (points, not dollars)
                if direction == "BUY":
                    favourable_points = (current_price - entry_price) * 100
                else:
                    favourable_points = (entry_price - current_price) * 100

                # -----------------------------------------------------------
                # Phase 2 — early breakeven once +BE_TRIGGER_POINTS reached
                # -----------------------------------------------------------
                if not be_moved and favourable_points >= BE_TRIGGER_POINTS:
                    if self.modify_sl(ticket_id, entry_price):
                        logger.info(
                            f"BE | ticket={ticket_id}, +{favourable_points:.1f}pt, "
                            f"SL→{entry_price}"
                        )
                        be_moved = True

                # -----------------------------------------------------------
                # Phase 3 — TP1 hit: close 50%, ensure SL at BE, notify
                # -----------------------------------------------------------
                if not tp1_hit:
                    reached = (
                        (direction == "BUY" and current_price >= tp1_level)
                        or (direction == "SELL" and current_price <= tp1_level)
                    )
                    if reached:
                        logger.info(
                            f"TP1 HIT | ticket={ticket_id}, price={current_price}, "
                            f"tp1={tp1_level}"
                        )

                        half_volume = round(pos.volume / 2, 2)
                        if half_volume >= 0.01:
                            self.close_partial(ticket_id, half_volume)

                        if not be_moved:
                            self.modify_sl(ticket_id, entry_price)
                            be_moved = True

                        self.db.update_trade(ticket_id, {
                            "exit_reason": "TP1_PARTIAL",
                        })
                        self.notifier.send_tp1_hit({
                            "direction": direction,
                            "ticket_id": ticket_id,
                            "tp1_price": tp1_level,
                            "entry_price": entry_price,
                            "tp2_price": pos.tp,
                            "account_type": self.config.active_account,
                        })
                        tp1_hit = True

                # -----------------------------------------------------------
                # Phase 4 — 90min time stop: force-close remainder
                # -----------------------------------------------------------
                if elapsed_minutes >= TIME_STOP_MINUTES:
                    logger.info(
                        f"TIME STOP | ticket={ticket_id}, "
                        f"{elapsed_minutes:.0f}min elapsed, force-closing"
                    )
                    if self.close_trade(ticket_id):
                        self.db.update_trade(ticket_id, {
                            "exit_reason": "TIME_STOP_90MIN",
                        })
                    break

        except Exception as e:
            logger.error(f"Monitor error for {ticket_id}: {e}")
        finally:
            self._monitor_threads.pop(ticket_id, None)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_mt5_position(self, ticket_id: int):
        """Get raw MT5 position object by ticket."""
        try:
            mt5 = self.market._import_mt5()
            positions = mt5.positions_get(ticket=ticket_id)
            if positions and len(positions) > 0:
                return positions[0]
            return None
        except Exception:
            return None

    def _verify_order(self, ticket_id: int) -> bool:
        """Verify an order was placed by checking open positions."""
        time.sleep(1)  # Brief delay for MT5 to process
        pos = self._get_mt5_position(ticket_id)
        return pos is not None
