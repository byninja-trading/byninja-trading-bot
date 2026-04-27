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
Risk management module for trading bot.

Provides risk statistics calculation, trade tracking, and performance metrics
for managing and monitoring trading bot risk exposure.
"""

import json
import threading
import time
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import asdict
from trading.persistence import PersistentMap
from trading.config import config_trading
from trading.risk.models import TradeStats, RiskStatistics
import copy

class RiskManager:
    """
    Risk management system for trading operations.
    
    Tracks trades, calculates statistics, and manages risk metrics.
    """
    
    def __init__(self, logger, bot_version: str):
        """
        Initialize risk manager.
        
        @param logger: Logger instance for logging messages
        @param bot_version: Version string for the bot
        """
        self.logger = logger
        self.bot_version = bot_version
        
        ## Files for data persistence
        self.closed_trades_file = f"closed_trades_v{bot_version}.pkl"
        self.report_file = f"risk_report_v{bot_version}.json"
        
        ## PersistentMap for trade data
        self.closed_trades = PersistentMap(self.closed_trades_file, logger)
        
        ## Current statistics
        self.stats = RiskStatistics(version=bot_version)
        
        ## Restore statistics from closed trades
        self._recalculate_stats()
        
        logger.info(f"📊 RiskManager initialized for version {bot_version}")
        logger.info(f"📈 Loaded {len(self.closed_trades)} closed trades")

    def add_closed_trade(self, symbol: str, entry_price: float, exit_price: float, 
                        quantity: float, pnl: float, pnl_percent: float):
        """
        Add a closed trade to statistics.
        
        @param symbol: Trading symbol
        @param entry_price: Entry price of the trade
        @param exit_price: Exit price of the trade
        @param quantity: Trade quantity
        @param pnl: Profit/loss amount
        @param pnl_percent: Profit/loss percentage
        """
        try:
            timestamp = time.time()
            trade_id = f"{symbol}_{timestamp}"
            
            trade_data = {
                'symbol': symbol,
                'entry_price': entry_price,
                'exit_price': exit_price,
                'quantity': quantity,
                'pnl': pnl,
                'pnl_percent': pnl_percent,
                'timestamp': timestamp,
                'date': datetime.now().isoformat()
            }
            
            ## Add the trade
            self.closed_trades[trade_id] = trade_data
            
            ## Asynchronously recalculate statistics
            threading.Thread(
                target=self._recalculate_stats_async, 
                args=(copy.deepcopy(dict(self.closed_trades)),),
                daemon=True
            ).start()
            
            self.logger.debug(f"📈 Added closed trade {symbol}: PnL ${pnl:.2f} ({pnl_percent:.2f}%)")
            
        except Exception as e:
            self.logger.error(f"❌ Error adding closed trade: {e}")

    def _recalculate_stats_async(self, trades_copy: Dict):
        """
        Asynchronously recalculate statistics from a copy of data.
        
        @param trades_copy: Dictionary copy of trades to calculate from
        """
        try:
            new_stats = self._calculate_stats(trades_copy)
            self.stats = new_stats
        except Exception as e:
            self.logger.error(f"❌ Error in async statistics recalculation: {e}")

    def _recalculate_stats(self):
        """Synchronously recalculate statistics."""
        try:
            self.stats = self._calculate_stats(dict(self.closed_trades))
        except Exception as e:
            self.logger.error(f"❌ Error in statistics recalculation: {e}")

    def _calculate_stats(self, trades_dict: Dict) -> RiskStatistics:
        """
        Calculate statistics from a given trades dictionary.
        
        @param trades_dict: Dictionary of trades to calculate statistics from
        @return: RiskStatistics object with calculated metrics
        """
        try:
            if not trades_dict:
                return RiskStatistics(version=self.bot_version, calculation_time=datetime.now().isoformat())
            
            trades = list(trades_dict.values())
            current_time = time.time()
            one_day_ago = current_time - 86400
            one_week_ago = current_time - 604800
            one_month_ago = current_time - 2592000
            initial_capital = config_trading.INITIAL_CAPITAL

            ## Group trades by symbol
            symbols_trades = {}
            for trade in trades:
                symbol = trade['symbol']
                if symbol not in symbols_trades:
                    symbols_trades[symbol] = []
                symbols_trades[symbol].append(trade)
            
            ## Create new statistics
            stats = RiskStatistics(version=self.bot_version, calculation_time=datetime.now().isoformat())
            stats.symbols_stats = {}
            
            ## Calculate statistics for each symbol
            for symbol, symbol_trades in symbols_trades.items():
                symbol_stats = TradeStats()
                symbol_stats.total_trades = len(symbol_trades)
                symbol_stats.total_volume = sum(trade['quantity'] * trade['entry_price'] for trade in symbol_trades)
                symbol_stats.total_pnl = sum(trade['pnl'] for trade in symbol_trades)
                symbol_stats.daily_pnl = sum(t['pnl'] for t in [t for t in symbol_trades if t['timestamp'] > one_day_ago])
                
                profitable_trades = [t for t in symbol_trades if t['pnl'] > 0]
                losing_trades = [t for t in symbol_trades if t['pnl'] < 0]
                
                symbol_stats.profitable_trades = len(profitable_trades)
                symbol_stats.total_profit = sum(t['pnl'] for t in profitable_trades)
                symbol_stats.total_loss = abs(sum(t['pnl'] for t in losing_trades))
                symbol_stats.largest_win = max([t['pnl'] for t in profitable_trades]) if profitable_trades else 0
                symbol_stats.largest_loss = min([t['pnl'] for t in losing_trades]) if losing_trades else 0
                symbol_stats.avg_profit = symbol_stats.total_profit / len(profitable_trades) if profitable_trades else 0
                symbol_stats.avg_loss = symbol_stats.total_loss / len(losing_trades) if losing_trades else 0
                symbol_stats.win_rate = (len(profitable_trades) / len(symbol_trades)) * 100 if symbol_trades else 0
                symbol_stats.profit_factor = symbol_stats.total_profit / symbol_stats.total_loss if symbol_stats.total_loss > 0 else float('inf')
                symbol_stats.daily_drawdown_percent = (abs(min(0, symbol_stats.daily_pnl)) / initial_capital) * 100
                symbol_stats.total_drawdown_percent = (abs(min(0, symbol_stats.total_pnl)) / initial_capital) * 100

                ## Calculate consecutive losses
                symbol_trades_sorted = sorted(symbol_trades, key=lambda x: x['timestamp'])
                current_loss_streak = 0
                for trade in reversed(symbol_trades_sorted):
                    if trade['pnl'] < 0:
                        current_loss_streak += 1
                    else:
                        break
                symbol_stats.consecutive_losses = current_loss_streak

                stats.symbols_stats[symbol] = symbol_stats

            ## Overall statistics
            stats.total_trades = len(trades)
            stats.total_volume = sum(trade['quantity'] * trade['entry_price'] for trade in trades)
            stats.total_pnl = sum(trade['pnl'] for trade in trades)
            
            ## Time-based metrics
            stats.daily_pnl = sum(trade['pnl'] for trade in trades if trade['timestamp'] > one_day_ago)
            stats.weekly_pnl = sum(trade['pnl'] for trade in trades if trade['timestamp'] > one_week_ago)
            stats.monthly_pnl = sum(trade['pnl'] for trade in trades if trade['timestamp'] > one_month_ago)

            ## Drawdown relative to capital
            stats.daily_drawdown_percent = (abs(min(0, stats.daily_pnl)) / initial_capital) * 100
            stats.total_drawdown_percent = (abs(min(0, stats.total_pnl)) / initial_capital) * 100

            return stats
            
        except Exception as e:
            self.logger.error(f"❌ Error calculating statistics: {e}")
            return RiskStatistics(version=self.bot_version, calculation_time=datetime.now().isoformat())

    def log_statistics(self):
        """Log current statistics."""
        try:
            stats = self.stats
            
            log_lines = []
            log_lines.append("📊 STATISTICS")
            log_lines.append(f"   Bot Version: {stats.version}")
            log_lines.append(f"   Calculation Time: {stats.calculation_time}")
            log_lines.append(f"   Total Trades: {stats.total_trades}")
            log_lines.append(f"   Total PnL: ${stats.total_pnl:.2f}")
            log_lines.append(f"   Daily PnL: ${stats.daily_pnl:.2f}")
            log_lines.append(f"   Weekly PnL: ${stats.weekly_pnl:.2f}")
            log_lines.append(f"   Monthly PnL: ${stats.monthly_pnl:.2f}")
            log_lines.append(f"   Daily Drawdown: {stats.daily_drawdown_percent:.2f}%")
            log_lines.append(f"   Total Drawdown: {stats.total_drawdown_percent:.2f}%")
            
            ## Statistics by symbol
            if stats.symbols_stats:
                log_lines.append("   📈 STATISTICS BY SYMBOL:")
                for symbol, symbol_stats in stats.symbols_stats.items():
                    log_lines.append(f"      🪙 {symbol}:")
                    log_lines.append(f"         Trades: {symbol_stats.total_trades}")
                    log_lines.append(f"         Total PnL: ${symbol_stats.total_pnl:.2f}")
                    log_lines.append(f"         Daily PnL: ${symbol_stats.daily_pnl:.2f}")
                    log_lines.append(f"         Win Rate: {symbol_stats.win_rate:.1f}%")
                    log_lines.append(f"         Profit Factor: {symbol_stats.profit_factor:.2f}")
                    log_lines.append(f"         Largest Win: ${symbol_stats.largest_win:.2f}")
                    log_lines.append(f"         Largest Loss: ${symbol_stats.largest_loss:.2f}")
                    log_lines.append(f"         Consecutive Losses: {symbol_stats.consecutive_losses}")
                    log_lines.append(f"         Daily Drawdown: {symbol_stats.daily_drawdown_percent:.2f}%")
                    log_lines.append(f"         Total Drawdown: {symbol_stats.total_drawdown_percent:.2f}%")
            else:
                log_lines.append("   📭 No symbol data available")
            
            self.logger.info("\n".join(log_lines))
            
        except Exception as e:
            self.logger.error(f"❌ Error logging statistics: {e}")

    def save_stats(self):
        """
        Generate and save JSON report.
        
        Creates a JSON report file with current statistics and saves it to disk.
        
        @return: Path to the generated report file, or None if save failed
        """
        try:
            stats_dict = asdict(self.stats)
            report_data = {
                "risk_report": {
                    "version": self.bot_version,
                    "generated_at": datetime.now().isoformat(),
                    "total_trades": len(self.closed_trades),
                    "statistics": stats_dict
                }
            }
            
            with open(self.report_file, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"💾 JSON report saved: {self.report_file}")
            return self.report_file
            
        except Exception as e:
            self.logger.error(f"❌ Error saving JSON report: {e}")
            return None

    def get_statistics(self) -> RiskStatistics:
        """
        Get current statistics.
        
        @return: Current RiskStatistics object
        """
        return self.stats

    def get_symbol_stats(self, symbol: str) -> Optional[TradeStats]:
        """
        Get statistics for a specific symbol.
        
        @param symbol: Symbol to get statistics for
        @return: TradeStats for the symbol, or None if symbol not found
        """
        return self.stats.symbols_stats.get(symbol)
