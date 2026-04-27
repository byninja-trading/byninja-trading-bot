#!/usr/bin/env python3

# Copyright 2026 byninja-trading
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
ByNinja Crypto Trading Bot.

An advanced automated trading bot for cryptocurrency trading on Binance
with intelligent entry/exit logic, risk management, and TCP control interface.

Run with: python3 -c "from trading.main import main; main()"
"""

import pandas as pd
import numpy as np
import time
import math
import threading
from typing import List, Dict, Optional, Tuple
import logging
from binance.client import Client

from trading.config import config_binance, config_trading
from logger.logger import Logger
from trading.persistence import PersistentMap
from trading.risk import RiskManager
from trading.models import OrderSide, OrderType, OrderStatus, Position, Order, SymbolControl

## Bot version
BOT_VERSION = "0.1.0"

## Logging configuration
logger = Logger(
    logger_name='TradingBot',
    log_file='trading_bot.log',
    console_level=logging.DEBUG,
    file_level=logging.DEBUG,
    general_level=logging.DEBUG
).get_logger()

## Main trading bot class

class ByNinjaTradingBot:
    """ByNinja trading bot with intelligent entry/exit and risk management."""
    
    def __init__(self):
        """Initialize the trading bot and Binance client."""
        self.capital = config_trading.INITIAL_CAPITAL
        self.client = None
        self.is_running = False
        self.active_positions = PersistentMap("active_positions.pkl", logger)
        self.pending_orders = PersistentMap("pending_orders.pkl", logger)
        self.symbol_controls = PersistentMap("symbol_controls.pkl", logger)
        self.risk_manager = RiskManager(logger, BOT_VERSION)

        logger.info(f"🥷 ByNinja Trading Bot initialization with capital: ${self.capital:.2f}")

        if not self.initialize_client():
            logger.error("❌ Failed to initialize Binance client")
            return

    def initialize_client(self):
        """
        Initialize Binance client and verify connection.
        
        @return: True if successful, False otherwise
        """
        try:
            self.client = Client(
                config_binance.BINANCE_API_KEY, 
                config_binance.BINANCE_API_SECRET, 
                testnet=False
            )
            
            ## Verify connection
            account = self.client.get_account()
            logger.info("✅ Successfully connected to Binance")
            
            ## Get available pairs
            exchange_info = self.client.get_exchange_info()
            available_symbols = [s["symbol"] for s in exchange_info["symbols"]]
            
            ## Filter available pairs
            self.available_pairs = [
                pair for pair in config_trading.TRADING_PAIRS 
                if pair in available_symbols
            ]
            
            logger.debug(f"🎯 Available trading pairs: {len(self.available_pairs)}")
            for pair in self.available_pairs:
                logger.debug(f"   - {pair}")
                
            return True
            
        except Exception as e:
            logger.error(f"❌ Error initializing Binance client: {e}")
            return False

    def start_trading(self):
        """Start trading and monitoring threads."""
        if self.is_running:
            logger.warning("⚠️ Bot is already running. Ignoring restart request.")
            return
        
        logger.info(f"🥷 STARTUP BYNINJA TRADING BOT v{BOT_VERSION}")

        self.is_running = True

        ## Start risk statistics monitoring thread
        risk_monitor_thread = threading.Thread(
            target=self._monitor_risk_statistics,
            daemon=True,
            name="RiskMonitor"
        )
        risk_monitor_thread.start()
        time.sleep(1)
        
        ## Start order monitoring thread
        order_monitor_thread = threading.Thread(
            target=self._monitor_pending_orders,
            daemon=True,
            name="OrderMonitor"
        )
        order_monitor_thread.start()

        ## Start monitoring threads for each symbol
        monitoring_lines = []
        monitoring_lines.append("📊 Started monitoring for:")
        for symbol in self.available_pairs:
            thread = threading.Thread(
                target=self._monitor_symbol,
                args=(symbol,),
                daemon=True,
                name=f"Monitor-{symbol}"
            )
            thread.start()
            monitoring_lines.append(f"   - {symbol}")

        ## Log all at once
        logger.info("\n".join(monitoring_lines))
        
        ## Start health monitor thread
        health_thread = threading.Thread(
            target=self._monitor_health_status, 
            daemon=True,
            name="HealthMonitor"
        )
        health_thread.start()
            
        logger.debug("✅ All systems started. Bot is active.")

    def _monitor_health_status(self):
        """
        Periodic system health monitoring.
        
        Logs system status at regular intervals.
        """
        while self.is_running:
            try:
                self.log_system_status()
                time.sleep(21600)
                
            except Exception as e:
                logger.error(f"❌ Error in health monitoring: {e}")
                time.sleep(600)

    def log_system_status(self):
        """
        Log detailed system status.
        
        Provides comprehensive status information including balances, positions,
        orders, and trading status for all symbols.
        """
        try:
            balance, detailed_balances = self._get_account_balance()
            
            ## Format status as single block
            status_lines = []
            
            ## General information
            status_lines.append("🖥️ STATUS")
            status_lines.append(f"💰 Total balance: ${balance:.2f}")
            status_lines.append(f"📈 Active positions: {len(self.active_positions)}")
            status_lines.append(f"🔄 Pending orders: {len(self.pending_orders)}")
            status_lines.append(f"🎯 Available pairs: {len(self.available_pairs)}")

            ## Detailed buy/sell status
            disabled_buying_symbols = []
            disabled_selling_symbols = []

            for symbol in self.available_pairs:
                buying_status, buying_reason = self.is_buying_enabled(symbol)
                selling_status, selling_reason = self.is_selling_enabled(symbol)
                
                if not buying_status:
                    disabled_buying_symbols.append((symbol, buying_reason))
                if not selling_status:
                    disabled_selling_symbols.append((symbol, selling_reason))

            status_lines.append(f"🛒 Buy status: {'🟢' if not disabled_buying_symbols else '🔴'}")
            if disabled_buying_symbols:
                status_lines.append(f"   🔴 Disabled for {len(disabled_buying_symbols)} pairs:")
                for symbol, reason in disabled_buying_symbols:
                    if reason:
                        status_lines.append(f"      - {symbol}: {reason}")
                    else:
                        status_lines.append(f"      - {symbol}")
                        
            status_lines.append(f"💰 Sell status: {'🟢' if not disabled_selling_symbols else '🔴'}")
            if disabled_selling_symbols:
                status_lines.append(f"   🔴 Disabled for {len(disabled_selling_symbols)} pairs:")
                for symbol, reason in disabled_selling_symbols:
                    if reason:
                        status_lines.append(f"      - {symbol}: {reason}")
                    else:
                        status_lines.append(f"      - {symbol}")

            ## Detailed active positions information
            if self.active_positions:
                total_invested = 0.0
                total_pnl = 0.0
                
                status_lines.append("📦 ACTIVE POSITIONS")
                
                for symbol, position in self.active_positions.items():
                    current_price = self._get_current_price(symbol)
                    pnl, pnl_percent = self._get_position_pnl(symbol, current_price)
                    position_value = position.quantity * current_price
                    total_invested += position_value
                    total_pnl += pnl

                    ## Calculate hold time
                    hold_time_seconds = time.time() - position.timestamp
                    hours = int(hold_time_seconds // 3600)
                    minutes = int((hold_time_seconds % 3600) // 60)
                    seconds = int(hold_time_seconds % 60)
                    formatted_time = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

                    status_lines.append(f"   🪙 {symbol}:")
                    status_lines.append(f"      Quantity: {position.quantity:.6f}")
                    status_lines.append(f"      Entry price: ${position.entry_price:.4f}")
                    status_lines.append(f"      Current price: ${current_price:.4f}")
                    status_lines.append(f"      PnL: ${pnl:+.2f} ({pnl_percent:+.2f}%)")
                    if position.trailing_active:
                        status_lines.append(f"      TS: ${position.trailing_stop_price:.4f} ({((position.trailing_stop_price - position.entry_price) / position.entry_price) * 100:.2f}%)")
                    status_lines.append(f"      TP: ${position.take_profit_price:.4f} (+{((position.take_profit_price - position.entry_price) / position.entry_price * 100):.2f}%)")
                    status_lines.append(f"      SL: ${position.stop_loss_price:.4f} (-{((position.entry_price - position.stop_loss_price) / position.entry_price * 100):.2f}%)")
                    status_lines.append(f"      Position value: ${position_value:.2f}")
                    status_lines.append(f"      Time: {formatted_time}")
                
                status_lines.append("📊 SUMMARY")
                status_lines.append(f"   💵 Total invested: ${total_invested:.2f}")
                status_lines.append(f"   📈 Total PnL: ${total_pnl:+.2f}")
                status_lines.append(f"   📉 Portfolio exposure: {(total_invested/self.capital)*100:.1f}%")
            else:
                status_lines.append("📭 No active positions")
            
            ## Pending orders information
            if self.pending_orders:
                status_lines.append("⏳ PENDING ORDERS")
                for order_id, order in self.pending_orders.items():
                    status_lines.append(f"   🆔 {order_id}: {order.side.value} {order.symbol} - {order.quantity:.6f} {order.type.value}")
            else:
                status_lines.append("✅ No pending orders")
            
            ## Log everything as one block
            logger.info("\n".join(status_lines))
            
        except Exception as e:
            logger.error(f"❌ Error getting system status: {e}")

    def _monitor_symbol(self, symbol: str):
        """
        Intelligent symbol monitoring with different intervals for entry/exit.
        
        Continuously monitors price action and executes trades based on
        configured strategies for the given symbol.
        
        @param symbol: Symbol to monitor
        """
        logger.debug(f"🔍 Intelligent monitoring for {symbol}")

        monitor_interval = 0.0
        current_price = 0.0
        
        while self.is_running:
            loop_start = time.time()

            try:
                has_position = symbol in self.active_positions
                current_price = self._get_current_price(symbol)

                if current_price == 0.0:
                    time.sleep(monitor_interval)
                    continue
                
                if has_position:
                    ## Continuous exit condition monitoring
                    self._monitor_exit_conditions(symbol, current_price)
                
                else:
                    ## Continuous entry condition monitoring
                    self._monitor_entry_conditions(symbol, current_price)

                time.sleep(monitor_interval)
            except Exception as e:
                logger.error(f"❌ Error monitoring {symbol}: {e}")
                time.sleep(5)

            ## Limit loop to 1 second
            loop_time = time.time() - loop_start
            sleep_time = max(0.0, 0.5 - loop_time)
            if sleep_time > 0:
                time.sleep(sleep_time)

    def _monitor_exit_conditions(self, symbol: str, current_price: float):
        """
        Continuous monitoring of exit conditions for active positions.
        
        Checks take profit, stop loss, and trailing stop conditions.
        
        @param symbol: Symbol with active position
        @param current_price: Current market price
        """
        try:
            if not self.is_selling_enabled(symbol)[0]:
                return

            if symbol not in self.active_positions:
                logger.warning(f"⚠️ {symbol} - No active position for exit monitoring")
                return

            position = self.active_positions[symbol]
            params = config_trading.TRADING_PARAMETERS[symbol]

            ## Check take profit
            if current_price >= position.take_profit_price:
                self._execute_sell(symbol, current_price, "TAKE PROFIT")
                return

            ## Check stop loss
            if current_price <= position.stop_loss_price:
                self._execute_sell(symbol, current_price, "STOP LOSS")
                return

            ## Check trailing stop
            pnl, pnl_percent = self._get_position_pnl(symbol, current_price)

            ## Activate trailing stop when profit target reached
            if not position.trailing_active and pnl_percent >= params["trail_activation_percent"]:
                position.trailing_active = True
                position.trailing_stop_price = current_price * (1 - params["trail_distance_percent"] / 100)
                self.active_positions[symbol] = position
                logger.info(f"🎯 {symbol} - TRAILING STOP activated (TS: {(pnl_percent - params['trail_distance_percent']):+.2f}%)")

            ## Update trailing stop only if price rises
            if position.trailing_active:
                new_trail_price = current_price * (1 - params["trail_distance_percent"] / 100)
                if new_trail_price > position.trailing_stop_price:
                    position.trailing_stop_price = new_trail_price
                    self.active_positions[symbol] = position

                ## Check trailing stop trigger
                if current_price <= position.trailing_stop_price:
                    self._execute_sell(symbol, current_price, f"TRAILING STOP")
                    return

            ## EMA20/EMA50 correction logic
            if time.time() - position.timestamp >= 120:

                df_1m = self._get_klines_df(symbol, "1m", 55)
                if df_1m is not None and len(df_1m) >= 50:

                    ## Update last candle
                    last_index = df_1m.index[-1]
                    df_1m.at[last_index, 'close'] = current_price
                    df_1m.at[last_index, 'high'] = max(df_1m.iloc[-1]["high"], current_price)
                    df_1m.at[last_index, 'low'] = min(df_1m.iloc[-1]["low"], current_price)

                    ## EMA20 and EMA50
                    df_1m["ema_20"] = df_1m["close"].ewm(span=20, adjust=False).mean()
                    df_1m["ema_50"] = df_1m["close"].ewm(span=50, adjust=False).mean()

                    ema20 = df_1m["ema_20"].iloc[-1]
                    ema50 = df_1m["ema_50"].iloc[-1]

                    ## Check conditions
                    current_close_below = current_price < ema20
                    prev_close_below = df_1m["close"].iloc[-2] < df_1m["ema_20"].iloc[-2]
                    touched_ema50 = df_1m["low"].iloc[-1] <= ema50 or df_1m["low"].iloc[-2] <= ema50

                    ## If below EMA20 and touched EMA50 → activate tight trailing
                    if current_close_below and prev_close_below and touched_ema50:
                        new_tight_trail = current_price * (1 - params["trail_tight_distance_percent"] / 100)

                        if not position.trailing_active:
                            position.trailing_active = True
                            position.trailing_stop_price = new_tight_trail
                            self.active_positions[symbol] = position
                            logger.info(f"📉 {symbol} — TIGHT TRAIL activated (TS: {(pnl_percent - params['trail_tight_distance_percent']):+.2f}%)")
                        elif new_tight_trail > position.trailing_stop_price:
                            position.trailing_stop_price = new_tight_trail
                            self.active_positions[symbol] = position
                            logger.info(f"📉 {symbol} — TIGHT TRAIL updated (TS: {(pnl_percent - params['trail_tight_distance_percent']):+.2f}%)")

            ## Logging
            if int(time.time()) % 30 == 0:
                hold_time_seconds = time.time() - position.timestamp
                hours = int(hold_time_seconds // 3600)
                minutes = int((hold_time_seconds % 3600) // 60)
                seconds = int(hold_time_seconds % 60)
                formatted_time = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                pnl_circle = "🟢" if pnl_percent > 0 else "🔴"

                logger.debug(
                    f"{symbol:<9} | EXIT  | "
                    f"${current_price:8.4f} | "
                    f"PnL: {pnl_percent:+.2f}% {pnl_circle} | "
                    + (f"TS: {((position.trailing_stop_price - position.entry_price) / position.entry_price * 100):+.2f}% | " if position.trailing_active else "")
                    + f"TP: +{((position.take_profit_price - position.entry_price) / position.entry_price * 100):.2f}% | "
                    f"SL: -{((position.entry_price - position.stop_loss_price) / position.entry_price * 100):.2f}% | "
                    + f"Time: {formatted_time}"
                )

        except Exception as e:
            logger.error(f"❌ Error monitoring exit for {symbol}: {e}")

    def _monitor_entry_conditions(self, symbol: str, current_price: float):
        """
        Monitor and validate conditions for market entry.
        
        Analyzes multiple technical indicators including EMAs, volume, and price
        action to determine if a position should be opened for the symbol.
        
        @param symbol: Trading symbol to monitor
        @param current_price: Current market price
        """
        try:
            if not self.is_buying_enabled(symbol)[0]:
                return

            if symbol in self.active_positions:
                logger.debug(f"⏸️ {symbol} already in open position, skipping buy")
                return

            params = config_trading.TRADING_PARAMETERS[symbol]

            ## 1️⃣ EMA200 SLOPE 3M
            df_3m = self._get_klines_df(symbol, "3m", 250)
            current_slope_ema200 = 0.0
            slope_ema200_passed = True

            if df_3m is not None and len(df_3m) > 210:
                df_3m["ema_200"] = df_3m["close"].ewm(span=200, adjust=False).mean()
                ema200_now_3m = df_3m["ema_200"].iloc[-1]
                ema200_prev_3m = df_3m["ema_200"].iloc[-5]
                current_slope_ema200 = (ema200_now_3m - ema200_prev_3m) / ema200_prev_3m * 100
                min_slope_ema200 = params["min_ema200_3m_slope"]

                if current_slope_ema200 < min_slope_ema200:
                    slope_ema200_passed = False

            ## 2️⃣ BOUNCE FROM EMA20
            df_1m = self._get_klines_df(symbol, "1m", 400)
            if df_1m is None or len(df_1m) < 350:
                return

            ## Update last candle
            last_index = df_1m.index[-1]
            df_1m.at[last_index, 'close'] = current_price
            df_1m.at[last_index, 'high'] = max(df_1m.iloc[-1]["high"], current_price)
            df_1m.at[last_index, 'low'] = min(df_1m.iloc[-1]["low"], current_price)

            ## Recalculate all indicators
            df_1m["ema_20"] = df_1m["close"].ewm(span=20, adjust=False).mean()
            df_1m["ema_50"] = df_1m["close"].ewm(span=50, adjust=False).mean()
            df_1m["ema_200"] = df_1m["close"].ewm(span=200, adjust=False).mean()

            ## Check for EMA20 touch on any of last 5 candles
            price_touched_ema20 = False
            for i in range(-6, -1):
                if df_1m["low"].iloc[i] <= df_1m["ema_20"].iloc[i]:
                    price_touched_ema20 = True
                    break

            ## Confirmation of bounce - only current candle
            bounce_confirmed = df_1m["close"].iloc[-2] > df_1m["ema_20"].iloc[-2]

            ## Filter for body breaking EMA20
            body_under_ema20 = df_1m["close"].iloc[-2] < df_1m["ema_20"].iloc[-2] and df_1m["open"].iloc[-2] < df_1m["ema_20"].iloc[-2]

            valid_bounce = price_touched_ema20 and bounce_confirmed and not body_under_ema20

            ## 3️⃣ DISTANCE BETWEEN EMA20 AND EMA50
            ema20_ema50_distance = (df_1m["ema_20"].iloc[-1] - df_1m["ema_50"].iloc[-1]) / df_1m["ema_50"].iloc[-1] * 100
            ema20_ema50_distance_passed = ema20_ema50_distance > params["min_ema20_ema50_distance"]

            ## 4️⃣ BREAKOUT CANDLE
            ## Look for breakout of highs on any of last 5 candles (via max)
            previous_highs_max = df_1m["high"].iloc[-7:-2].max()
            breakout_confirmed = df_1m["close"].iloc[-2] > previous_highs_max

            ## 5️⃣ VOLUME SPIKE (with coefficient from config)
            volume_ma = df_1m["volume"].rolling(20).mean().iloc[-2]
            current_volume = df_1m["volume"].iloc[-2]
            volume_ratio = current_volume / volume_ma
            volume_spike = volume_ratio > params["volume_spike_coeff"]

            ## 6️⃣ NO OVERHEAT (with parameter from config)
            candle_size = (df_1m["high"].iloc[-2] - df_1m["low"].iloc[-2]) / df_1m["close"].iloc[-2] * 100
            reasonable_candle = candle_size < params["max_candle_size"]

            ## 7️⃣ DISTANCE BETWEEN EMA50 AND EMA200
            ema50_ema200_distance = (df_1m["ema_50"].iloc[-1] - df_1m["ema_200"].iloc[-1]) / df_1m["ema_200"].iloc[-1] * 100
            ema50_ema200_distance_passed = ema50_ema200_distance > params["min_ema50_ema200_distance"]

            ## 8️⃣ EMA20 SLOPE 1M
            ema20_now = df_1m["ema_20"].iloc[-1]
            ema20_prev = df_1m["ema_20"].iloc[-3]
            current_slope_ema20 = (ema20_now - ema20_prev) / ema20_prev * 100
            slope_ema20_passed = current_slope_ema20 > params["min_ema20_1m_slope"]

            ## 9️⃣ EMA50 SLOPE 1M
            ema50_now = df_1m["ema_50"].iloc[-1]
            ema50_prev = df_1m["ema_50"].iloc[-3]
            current_slope_ema50 = (ema50_now - ema50_prev) / ema50_prev * 100
            slope_ema50_passed = current_slope_ema50 > params["min_ema50_1m_slope"]

            ## FINAL CHECK OF ALL POINTS
            if (valid_bounce and 
                breakout_confirmed and 
                volume_spike and 
                reasonable_candle and 
                slope_ema200_passed and
                slope_ema20_passed and
                slope_ema50_passed and
                ema50_ema200_distance_passed and
                ema20_ema50_distance_passed):

                reason = (
                    f"BOUNCE\n"
                    f"      Volume: {volume_ratio:4.1f}x\n"
                    f"      Candle: {candle_size:.2f}%\n"
                    f"      DEMA200/50: {ema50_ema200_distance:.3f}%\n"
                    f"      DEMA50/20: {ema20_ema50_distance:.3f}%\n"
                    f"      S20: {current_slope_ema20:+.3f}%\n"
                    f"      S50: {current_slope_ema50:+.3f}%\n"
                    f"      S200: {current_slope_ema200:+.3f}%"
                )

                self._execute_buy(
                    symbol, 
                    current_price, 
                    reason
                )

            if int(time.time()) % 30 == 0:
                logger.debug(
                    f"{symbol:<9} | ENTRY | "
                    f"${current_price:8.4f} | "
                    f"S200 {current_slope_ema200:+.3f}%>{params['min_ema200_3m_slope']:+.3f}% {'🟢' if slope_ema200_passed else '🔴'} | "
                    f"S50 {current_slope_ema50:+.3f}%>{params['min_ema50_1m_slope']:+.3f}% {'🟢' if slope_ema50_passed else '🔴'} | "
                    f"S20 {current_slope_ema20:+.3f}%>{params['min_ema20_1m_slope']:+.3f}% {'🟢' if slope_ema20_passed else '🔴'} | "
                    f"D200/50 {ema50_ema200_distance:+.3f}%>{params['min_ema50_ema200_distance']:+.3f}% {'🟢' if ema50_ema200_distance_passed else '🔴'} | "
                    f"D50/20 {ema20_ema50_distance:+.3f}%>{params['min_ema20_ema50_distance']:+.3f}% {'🟢' if ema20_ema50_distance_passed else '🔴'} | "
                    f"Vol {volume_ratio:4.1f}x>{params['volume_spike_coeff']}x {'🟢' if volume_spike else '🔴'}"
                )
        except Exception as e:
            logger.error(f"❌ Error checking entry for {symbol}: {e}")

    def _execute_sell(self, symbol: str, price: float, reason: str):
        """
        Execute a sell order for the symbol.
        
        @param symbol: Symbol to sell
        @param price: Current market price
        @param reason: Reason for selling
        """
        try:
            if symbol not in self.active_positions:
                logger.warning(f"⚠️ {symbol} - No active position to sell")
                return
            
            for order_id, order in self.pending_orders.items():
                if order.symbol == symbol and order.side == OrderSide.SELL:
                    logger.debug(f"⏸️ {symbol} - Already has pending sell order, skipping")
                    return

            position = self.active_positions[symbol]
            order_id = self.place_order(
                symbol = symbol,
                side = OrderSide.SELL,
                quantity = position.quantity,
                reason = reason,
                price = price
            )
            
            if order_id:
                logger.debug(f"📤 {symbol} - Sell order placed. Current price: ${price}")
            else:
                logger.error(f"❌ {symbol} - Failed to place sell order")
                        
        except Exception as e:
            logger.error(f"❌ Error selling {symbol}: {e}")

    def _execute_buy(self, symbol: str, price: float, reason: str):
        """
        Execute a buy order for the symbol.
        
        @param symbol: Symbol to buy
        @param price: Current market price
        @param reason: Reason for buying
        """
        try:
            for order_id, order in self.pending_orders.items():
                if order.symbol == symbol and order.side == OrderSide.BUY:
                    logger.debug(f"⏸️ {symbol} - Already has pending buy order, skipping")
                    return

            ## Get ready quantity
            quantity, message = self.calculate_position_quantity(symbol, price)
            if quantity <= 0:
                logger.warning(f"⏹️ {symbol} - Not buying: {message}")
                return

            order_id = self.place_order(
                symbol = symbol,
                side = OrderSide.BUY,
                quantity = quantity,
                reason = reason,
                price = price
            )
            
            if order_id:
                logger.debug(f"📥 {symbol} - Buy order placed. Price: ${price}")
            else:
                logger.error(f"❌ {symbol} - Failed to place buy order")
                    
        except Exception as e:
            logger.error(f"❌ Error buying {symbol}: {e}")


    def place_order(self, symbol: str, side: OrderSide, quantity: float, reason: str,
                   order_type: OrderType = OrderType.MARKET, price: Optional[float] = None) -> Optional[str]:
        """
        Place a real order on Binance.
        
        @param symbol: Trading symbol
        @param side: Order side (BUY or SELL)
        @param quantity: Order quantity
        @param reason: Reason for the order
        @param order_type: Type of order (MARKET or LIMIT)
        @param price: Order price (for LIMIT orders)
        @return: Order ID or None if failed
        """
        try:
            if quantity <= 0:
                logger.error(f"❌ Invalid quantity for {symbol}: {quantity:.8f}")
                return None

            result = None

            if order_type == OrderType.MARKET:
                if side == OrderSide.BUY:
                    result = self.client.order_market_buy(
                        symbol=symbol,
                        quantity=quantity
                    )
                else:  ## SELL
                    result = self.client.order_market_sell(
                        symbol=symbol,
                        quantity=quantity
                    )
            else:
                logger.error(f"❌ Unsupported order type: {order_type}")
                return None
            
            ## Check result
            if not result:
                logger.error(f"❌ Error: empty order result for {symbol}")
                return None
            
            ## Always consider order NEW when created, monitoring will check real status
            order = Order(
                symbol=symbol,
                side=side,
                type=order_type,
                quantity=quantity,
                price=price,
                status=OrderStatus.NEW
            )
            
            ## Log order information
            order_lines = []
            order_lines.append(f"📝 ORDER PLACED {side.value} {symbol}")
            order_lines.append(f"   Type: {order_type.value}")
            order_lines.append(f"   Reason: {reason}")
            order_lines.append(f"   Quantity: {quantity:.8f}")
            order_lines.append(f"   Current price: ${price:.4f}")
            order_lines.append(f"   Order ID: {result['orderId']}")
            order_lines.append(f"   Exchange status: {result['status']}")
            
            logger.info("\n".join(order_lines))
            
            ## Store in persistent map
            self.pending_orders[result['orderId']] = order
            return result['orderId']
            
        except Exception as e:
            logger.error(f"❌ Error placing order {symbol}: {e}")
            return None

    def _monitor_pending_orders(self):
        """
        Monitor status of pending orders with detailed logging.
        
        Checks order status on the exchange and processes filled orders.
        """
        while self.is_running:
            try:
                orders_to_remove = []
                
                for order_id, order in self.pending_orders.items():
                    try:
                        ## Check order status on exchange
                        order_info = self.client.get_order(symbol=order.symbol, orderId=order_id)
                        
                        if order_info['status'] == 'FILLED':
                            ## DETAILED LOGGING FOR FILLED ORDERS
                            if order.side == OrderSide.BUY:
                                self._process_successful_buy(order_id, order, order_info)
                            else:  ## SELL
                                self._process_successful_sell(order_id, order, order_info)
                            
                            ## Mark for removal
                            orders_to_remove.append(order_id)
                            
                        elif order_info['status'] in ['CANCELED', 'REJECTED', 'EXPIRED']:
                            logger.warning(f"❌ Order {order_id} canceled/rejected: {order_info['status']}")
                            orders_to_remove.append(order_id)
                            
                    except Exception as e:
                        logger.error(f"❌ Error checking order {order_id}: {e}")
                        ## If order not found on exchange, remove it
                        if "Order does not exist" in str(e):
                            logger.warning(f"🗑️ Order {order_id} not found on exchange, removing")
                            orders_to_remove.append(order_id)
                
                ## Remove processed orders
                for order_id in orders_to_remove:
                    del self.pending_orders[order_id]
                
                time.sleep(5)  ## Check every 5 seconds
                
            except Exception as e:
                logger.error(f"❌ Error monitoring orders: {e}")
                time.sleep(10)

    def _process_successful_buy(self, order_id: str, order: Order, order_info: dict):
        """
        Process a successful buy order.
        
        Creates a position record with take profit and stop loss levels.
        
        @param order_id: Order ID
        @param order: Order object
        @param order_info: Order info from exchange
        """
        try:
            total_cost = float(order_info['cummulativeQuoteQty'])
            executed_price = total_cost / float(order.quantity)
            
            ## Get parameters for symbol
            if order.symbol in config_trading.TRADING_PARAMETERS:
                params = config_trading.TRADING_PARAMETERS[order.symbol]

                take_profit_price = executed_price * (1 + params["take_profit_percent"] / 100)
                stop_loss_price = executed_price * (1 - params["stop_loss_percent"] / 100)

                ## Get current balance
                current_balance, _ = self._get_account_balance()
                
                ## Format detailed log as single block
                buy_lines = []
                buy_lines.append(f"🟡 {order.symbol} - BUY executed")
                buy_lines.append(f"   🆔 Order ID: {order_id}")
                buy_lines.append(f"   💰 Spent: ${total_cost:.2f}")
                buy_lines.append(f"   🪙 Quantity: {order.quantity:.6f}")
                buy_lines.append(f"   📊 Execution price: ${executed_price:.4f}")
                buy_lines.append(f"   🎯 Take Profit: ${take_profit_price:.4f} (+{params['take_profit_percent']}%)")
                buy_lines.append(f"   🛡️  Stop Loss: ${stop_loss_price:.4f} (-{params['stop_loss_percent']}%)")
                buy_lines.append(f"   💵 Current balance: ${current_balance:.2f}")
                
                logger.info("\n".join(buy_lines))
                
                ## Create position
                position = Position(
                    symbol=order.symbol,
                    side=OrderSide.BUY,
                    quantity=order.quantity,
                    entry_price=executed_price,
                    timestamp=time.time(),
                    take_profit_price=take_profit_price,
                    stop_loss_price=stop_loss_price,
                )
                
                self.active_positions[order.symbol] = position
                
            else:
                logger.error(f"❌ No parameters found for {order.symbol}")
                
        except Exception as e:
            logger.error(f"❌ Error logging buy: {e}")

    def _process_successful_sell(self, order_id: str, order: Order, order_info: dict):
        """
        Process a successful sell order.
        
        Logs PnL, removes position, and updates risk manager statistics.
        
        @param order_id: Order ID
        @param order: Order object
        @param order_info: Order info from exchange
        """
        try:
            executed_price = float(order_info['cummulativeQuoteQty']) / float(order.quantity)
            
            ## Find corresponding position
            if order.symbol in self.active_positions:
                position = self.active_positions[order.symbol]
                
                ## Calculate PnL
                initial_cost = position.entry_price * position.quantity
                final_amount = executed_price * position.quantity
                pnl = final_amount - initial_cost
                pnl_percent = (executed_price - position.entry_price) / position.entry_price * 100
                
                ## Get current balance
                current_balance, _ = self._get_account_balance()
                
                ## Format detailed log as single block
                sell_lines = []
                if pnl_percent >= 0.2:
                    sell_lines.append(f"🟢 {order.symbol} - SELL executed")
                else:
                    sell_lines.append(f"🔴 {order.symbol} - SELL executed")
                sell_lines.append(f"   🆔 Order ID: {order_id}")
                sell_lines.append(f"   💰 Initial investment: ${initial_cost:.2f}")
                sell_lines.append(f"   💵 Received: ${final_amount:.2f}")
                sell_lines.append(f"   📈 Net PnL: ${pnl:+.2f} ({pnl_percent:+.2f}%)")
                sell_lines.append(f"   🪙 Quantity: {position.quantity:.6f}")
                sell_lines.append(f"   📊 Execution price: ${executed_price:.4f}")
                sell_lines.append(f"   💵 Current balance: ${current_balance:.2f}")
                
                logger.info("\n".join(sell_lines))
                
                ## Remove position
                del self.active_positions[order.symbol]

                self.risk_manager.add_closed_trade(
                    symbol=order.symbol,
                    entry_price=position.entry_price,
                    exit_price=executed_price,
                    quantity=position.quantity,
                    pnl=pnl,
                    pnl_percent=pnl_percent
                )
            else:
                logger.warning(f"⚠️ Position for {order.symbol} not found on sell")
                
        except Exception as e:
            logger.error(f"❌ Error logging sell: {e}")

    def get_symbol_info(self, symbol: str) -> Optional[Dict]:
        """
        Get trading rules for a symbol.
        
        @param symbol: Trading symbol
        @return: Symbol information or None
        """
        try:
            if not self.client:
                return None
                
            info = self.client.get_symbol_info(symbol)
            return info
        except Exception as e:
            logger.error(f"❌ Error getting info for {symbol}: {e}")
            return None

    def adjust_quantity(self, symbol: str, quantity: float) -> float:
        """
        Adjust quantity according to symbol's rules.
        
        @param symbol: Trading symbol
        @param quantity: Quantity to adjust
        @return: Adjusted quantity
        """
        try:
            info = self.get_symbol_info(symbol)
            if not info:
                logger.warning(f"⚠️ Could not get info for {symbol}")
                return 0.0
                
            for filter_obj in info['filters']:
                if filter_obj['filterType'] == 'LOT_SIZE':
                    step_size = float(filter_obj['stepSize'])
                    min_qty = float(filter_obj['minQty'])
                    max_qty = float(filter_obj.get('maxQty', 1000000))
                    
                    ## Round down to multiple of step_size
                    adjusted_qty = math.floor(quantity / step_size) * step_size
                    
                    ## Check min/max quantity
                    final_qty = max(min(adjusted_qty, max_qty), min_qty)
                    
                    ## Additional rounding to correct decimal places
                    precision = int(round(-math.log(step_size, 10), 0))
                    final_qty = round(final_qty, precision)

                    if abs(final_qty - quantity) > step_size:
                        logger.debug(f"🔧 {symbol} - Quantity adjusted: {quantity:.8f} -> {final_qty:.8f}")
                    
                    return final_qty
                    
            return quantity
        except Exception as e:
            logger.error(f"❌ Error adjusting quantity {symbol}: {e}")
            return 0.0

    def calculate_position_quantity(self, symbol: str, current_price: float) -> Tuple[float, str]:
        """
        Calculate quantity for a new position.
        
        @param symbol: Trading symbol
        @param current_price: Current market price
        @return: Tuple of (quantity, message)
        """
        try:
            if symbol not in config_trading.TRADING_PARAMETERS:
                return 0.0, f"No parameters found for {symbol}"
                
            params = config_trading.TRADING_PARAMETERS[symbol]
            base_size_usd = self.capital * (params["position_size"] / 100)
            
            ## Check maximum exposure
            current_exposure = 0.0
            for pos_symbol, position in self.active_positions.items():
                pos_current_price = self._get_current_price(pos_symbol)
                current_exposure += position.quantity * pos_current_price
            max_exposure = self.capital * (config_trading.RISK_PARAMETERS["max_portfolio_exposure"] / 100)
            
            if current_exposure + base_size_usd > max_exposure:
                available = max(0, max_exposure - current_exposure)
                base_size_usd = min(base_size_usd, available)
                if base_size_usd < self.capital * 0.005:
                    return 0.0, "Maximum portfolio exposure reached"
            
            ## Calculate initial quantity
            quantity = base_size_usd / current_price
            
            ## Adjust quantity according to symbol rules
            adjusted_quantity = self.adjust_quantity(symbol, quantity)
            
            if adjusted_quantity <= 0:
                return 0.0, "Adjusted quantity too small"
                
            ## Calculate final size in USD for logging
            final_size_usd = adjusted_quantity * current_price
            
            logger.debug(f"📏 {symbol} - Position size: ${final_size_usd:.2f} ({adjusted_quantity:.6f})")
            
            return adjusted_quantity, "OK"
            
        except Exception as e:
            logger.error(f"❌ Error calculating quantity for {symbol}: {e}")
            return 0.0, f"Calculation error: {e}"

    def _get_account_balance(self) -> Tuple[float, Dict]:
        """
        Get account balance and asset breakdown.
        
        @return: Tuple of (total_balance, balances_dict)
        """
        try:
            if not self.client:
                logger.error("❌ Client not initialized")
                return 0.0, {}
                
            account = self.client.get_account()
            balances = {}
            total_balance = 0.0
            
            for balance in account['balances']:
                asset = balance['asset']
                free = float(balance['free'])
                locked = float(balance['locked'])
                total = free + locked
                
                if total > 0:
                    balances[asset] = {
                        'free': free,
                        'locked': locked,
                        'total': total
                    }
                    
                    if asset == 'USDT':
                        total_balance += total
            
            logger.debug(f"💰 Balance: USDT=${total_balance:.2f}, assets: {len(balances)}")
            return total_balance, balances
            
        except Exception as e:
            logger.error(f"❌ Error getting account balance: {e}")
            return 0.0, {}

    def _get_current_price(self, symbol: str) -> float:
        """
        Get current market price for symbol.
        
        @param symbol: Trading symbol
        @return: Current price or 0.0 if error
        """
        try:
            ticker = self.client.get_symbol_ticker(symbol=symbol)
            return float(ticker['price'])
        except Exception as e:
            logger.error(f"❌ Error getting price for {symbol}: {e}")
            return 0.0

    def _get_position_pnl(self, symbol: str, current_price: float) -> Tuple[float, float]:
        """
        Calculate PnL and PnL% for position.
        
        @param symbol: Trading symbol
        @param current_price: Current market price
        @return: Tuple of (pnl_amount, pnl_percent)
        """
        try:
            position = self.active_positions[symbol]
            pnl = (current_price - position.entry_price) * position.quantity
            pnl_percent = (current_price - position.entry_price) / position.entry_price * 100

            return pnl, pnl_percent
        except Exception as e:
            logger.error(f"❌ Error calculating PnL for {symbol}: {e}")
            return 0.0, 0.0

    def _get_klines_df(self, symbol: str, interval: str = "5m", limit: int = 50) -> Optional[pd.DataFrame]:
        """
        Load and format DataFrame with klines for a symbol.
        
        @param symbol: Trading symbol
        @param interval: Kline interval (e.g., "1m", "5m", "1h")
        @param limit: Number of klines to fetch
        @return: DataFrame with kline data or None if invalid/incomplete
        """
        try:
            klines = self.client.get_klines(symbol=symbol, interval=interval, limit=limit)
            if not klines or len(klines) < 10:
                return None

            df = pd.DataFrame(klines, columns=[
                "open_time", "open", "high", "low", "close", "volume",
                "close_time", "qav", "num_trades", "taker_base", "taker_quote", "ignore"
            ])

            ## Convert needed columns to numbers
            for col in ["open", "high", "low", "close", "volume"]:
                df[col] = pd.to_numeric(df[col], errors="coerce")

            df = df.dropna()
            return df if len(df) > 3 else None

        except Exception as e:
            logger.error(f"❌ Failed to get klines for {symbol}: {e}")
            return None

    def force_sell(self, symbol: Optional[str] = None):
        """
        Manually sell position for a symbol or all symbols.
        
        @param symbol: Symbol to sell, or None to sell all
        """
        def _sell_single(sym: str):
            """Sell a single symbol"""
            if sym not in self.active_positions:
                logger.warning(f"⚠️  {sym} - no active position to force sell")
                return

            current_price = self._get_current_price(sym)
            self._execute_sell(sym, current_price, "TELEGRAM FORCE SELL")

        try:
            if symbol is None:
                ## Sell all active positions
                if not self.active_positions:
                    logger.warning("⚠️  No active positions to force sell")
                    return

                symbols_to_sell = list(self.active_positions.keys())

                for sym in symbols_to_sell:
                    _sell_single(sym)

            else:
                ## Sell specific symbol
                _sell_single(symbol)

        except Exception as e:
            logger.error(f"❌ Error force selling {symbol}: {e}")

    def force_buy(self, symbol: Optional[str] = None):
        """
        Manually buy position for a symbol or all symbols.
        
        @param symbol: Symbol to buy, or None to buy all
        """
        def _buy_single(sym: str):
            """Buy a single symbol"""
            if sym in self.active_positions:
                logger.warning(f"⚠️  {sym} - already has active position for force buy")
                return

            current_price = self._get_current_price(sym)
            self._execute_buy(sym, current_price, "TELEGRAM FORCE BUY")

        try:
            if symbol is None:
                ## Buy all available symbols
                symbols_to_buy = [sym for sym in self.available_pairs if sym not in self.active_positions]

                if not symbols_to_buy:
                    logger.warning("⚠️  All symbols in active position")
                    return

                for sym in symbols_to_buy:
                    _buy_single(sym)

            else:
                ## Buy specific symbol
                _buy_single(symbol)

        except Exception as e:
            logger.error(f"❌ Error force buying {symbol}: {e}")

    def stop_trading(self):
        """
        Stop trading and gracefully shutdown.
        
        Saves statistics and logs final status.
        """
        if not self.is_running:
            logger.warning("⚠️  Bot already stopped.")
            return

        self.is_running = False

        self.risk_manager.save_stats()
        
        self.log_system_status()
        time.sleep(1)
        logger.info(f"🛑 STOP BYNINJA TRADING BOT v{BOT_VERSION}...")

    def _monitor_risk_statistics(self):
        """
        Monitor risk statistics and enforce risk management rules.
        
        Runs in separate thread to check portfolio drawdown and symbol-specific
        risk parameters, disabling buying when limits are exceeded.
        """
        last_update_time = None

        while self.is_running:
            try:
                ## Check if statistics updated
                stats = self.risk_manager.get_statistics()
                if stats and stats.calculation_time != last_update_time:
                    last_update_time = stats.calculation_time

                    ## Check total drawdown for all symbols
                    if stats.total_drawdown_percent >= config_trading.RISK_PARAMETERS["max_total_drawdown"]:
                        self.disable_buying(None, f"Total drawdown ALL symbols {stats.total_drawdown_percent:.2f}%")
                    ## Check daily drawdown for all symbols
                    elif stats.daily_drawdown_percent >= config_trading.RISK_PARAMETERS["max_daily_drawdown"]:
                        self.disable_buying(None, f"Daily drawdown ALL symbols {stats.daily_drawdown_percent:.2f}%")

                    for symbol, symbol_stats in stats.symbols_stats.items():
                        if not self.is_buying_enabled(symbol)[0]:
                            continue  ## Skip if already disabled

                        ## Check total drawdown for symbol
                        if symbol_stats.total_drawdown_percent >= config_trading.RISK_PARAMETERS["max_total_drawdown_per_symbol"]:
                            self.disable_buying(symbol, f"Total drawdown {symbol_stats.total_drawdown_percent:.2f}%")
                        ## Check daily drawdown for symbol
                        elif symbol_stats.daily_drawdown_percent >= config_trading.RISK_PARAMETERS["max_daily_drawdown_per_symbol"]:
                            self.disable_buying(symbol, f"Daily drawdown {symbol_stats.daily_drawdown_percent:.2f}%")
                        ## Check consecutive losses
                        elif symbol_stats.consecutive_losses >= config_trading.RISK_PARAMETERS["max_consecutive_losses"]:
                            self.disable_buying(symbol, f"{symbol_stats.consecutive_losses} consecutive losses")

                time.sleep(5)  ## Check every 5 seconds

            except Exception as e:
                logger.error(f"❌ Error monitoring risks: {e}")
                time.sleep(300)  ## Wait 5 minutes on error

    def _set_trading_status(self, symbol: Optional[str], operation: str, enabled: bool, reason: Optional[str] = None):
        """
        Universal function for setting trading status.
        
        @param symbol: Symbol to update, or None for all
        @param operation: "buying" or "selling"
        @param enabled: Enable or disable trading
        @param reason: Reason for the change
        """
        def _set_single_symbol(sym: str):
            """Set status for a single symbol"""
            if sym not in self.available_pairs:
                logger.error(f"❌ Symbol {sym} not found in available pairs")
                return

            control = self.symbol_controls.get(sym, SymbolControl())
            current_enabled = control.buying_enabled if operation == "buying" else control.selling_enabled

            ## Check if status already matches desired
            if current_enabled == enabled:
                logger.info(f"⚠️ {operation} for {sym} already {'enabled' if enabled else 'disabled'}")
                return

            ## Update status
            if operation == "buying":
                control.buying_enabled = enabled
                control.disabled_buy_reason = reason
            else:
                control.selling_enabled = enabled
                control.disabled_sell_reason = reason

            self.symbol_controls[sym] = control

            ## Log changes
            icon = "🟢" if enabled else "🔴"
            action = "Enabled" if enabled else "Disabled"
            log_message = f"{icon} {action} {operation} for {sym}"
            if reason:
                log_message += f": {reason}"

            if enabled:
                logger.info(log_message)
            else:
                logger.warning(log_message)

        ## Execute for one symbol or all
        if symbol:
            _set_single_symbol(symbol)
        else:
            for available_symbol in self.available_pairs:
                _set_single_symbol(available_symbol)

    def disable_buying(self, symbol: Optional[str] = None, reason: Optional[str] = None):
        """
        Disable buying for symbol or all symbols.
        
        @param symbol: Symbol to disable, or None for all
        @param reason: Reason for disabling
        """
        self._set_trading_status(symbol, "buying", False, reason)

    def enable_buying(self, symbol: Optional[str] = None, reason: Optional[str] = None):
        """
        Enable buying for symbol or all symbols.
        
        @param symbol: Symbol to enable, or None for all
        @param reason: Reason for enabling
        """
        self._set_trading_status(symbol, "buying", True, reason)

    def disable_selling(self, symbol: Optional[str] = None, reason: Optional[str] = None):
        """
        Disable selling for symbol or all symbols.
        
        @param symbol: Symbol to disable, or None for all
        @param reason: Reason for disabling
        """
        self._set_trading_status(symbol, "selling", False, reason)

    def enable_selling(self, symbol: Optional[str] = None, reason: Optional[str] = None):
        """
        Enable selling for symbol or all symbols.
        
        @param symbol: Symbol to enable, or None for all
        @param reason: Reason for enabling
        """
        self._set_trading_status(symbol, "selling", True, reason)

    def is_buying_enabled(self, symbol: str) -> tuple[bool, Optional[str]]:
        """
        Check if buying is enabled for symbol.
        
        @param symbol: Trading symbol
        @return: Tuple of (enabled_bool, reason_string)
        """
        control = self.symbol_controls.get(symbol)
        if control:
            return control.buying_enabled, control.disabled_buy_reason
        return True, None

    def is_selling_enabled(self, symbol: str) -> tuple[bool, Optional[str]]:
        """
        Check if selling is enabled for symbol.
        
        @param symbol: Trading symbol
        @return: Tuple of (enabled_bool, reason_string)
        """
        control = self.symbol_controls.get(symbol)
        if control:
            return control.selling_enabled, control.disabled_sell_reason
        return True, None