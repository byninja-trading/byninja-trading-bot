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
Risk management data models.

Provides dataclasses for trade statistics and risk metrics tracking.
"""

from dataclasses import dataclass, asdict
from typing import Dict


@dataclass
class TradeStats:
    """
    Trade statistics dataclass.
    
    Aggregates performance metrics for individual trades or symbols.
    """
    total_trades: int = 0
    profitable_trades: int = 0
    total_profit: float = 0.0
    total_loss: float = 0.0
    largest_win: float = 0.0
    largest_loss: float = 0.0
    avg_profit: float = 0.0
    avg_loss: float = 0.0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    total_volume: float = 0.0
    total_pnl: float = 0.0
    daily_pnl: float = 0.0
    consecutive_losses: int = 0
    daily_drawdown_percent = 0.0
    total_drawdown_percent = 0.0


@dataclass
class RiskStatistics:
    """
    Risk statistics dataclass.
    
    Aggregates overall risk metrics and statistics across all trades and symbols.
    """
    version: str
    total_trades: int = 0
    total_volume: float = 0.0
    total_pnl: float = 0.0
    daily_pnl: float = 0.0
    weekly_pnl: float = 0.0
    monthly_pnl: float = 0.0
    daily_drawdown_percent = 0.0
    total_drawdown_percent = 0.0
    symbols_stats: Dict[str, 'TradeStats'] = None
    calculation_time: str = None
    
    def __post_init__(self):
        if self.symbols_stats is None:
            self.symbols_stats = {}