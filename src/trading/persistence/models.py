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
Test data models for persistent map testing.

Provides enumeration and dataclass definitions for testing persistent storage
of trading data structures (positions, orders, etc.).
"""

from enum import Enum
from dataclasses import dataclass


## Order side enumeration for trading

class OrderSide(Enum):
    """
    Order side enumeration.
    
    Specifies the direction of a trading order (buy or sell).
    """
    BUY = "BUY"
    SELL = "SELL"


## Position data class for testing

@dataclass
class Position:
    """
    Position data class for testing persistent map.
    
    Represents a trading position with entry/exit points and P&L tracking.
    Used for testing persistence of complex objects in persistent map.
    """
    
    ## Trading pair symbol (e.g., BTCUSDT)
    symbol: str
    
    ## Order side (BUY or SELL)
    side: OrderSide
    
    ## Position quantity
    quantity: float = 1.0
    
    ## Entry price for this position
    entry_price: float = 0.5
    
    ## Current market price for P&L calculation
    current_price: float = 0.5
    
    ## Profit/Loss in absolute value
    pnl: float = 0.2
    
    ## Profit/Loss in percentage
    pnl_percent: float = 1.0
    
    ## Unix timestamp of position entry
    timestamp: float = 1.0
    
    ## Take profit target price
    take_profit: float = 0.0
    
    ## Stop loss price level
    stop_loss: float = 0.0
