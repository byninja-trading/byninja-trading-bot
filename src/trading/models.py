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
Trading data models and enums.

Provides enumerations and dataclasses for order management, position tracking,
and symbol control in the trading bot.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional


class OrderSide(Enum):
    """
    Order side enumeration (BUY or SELL).
    
    Defines the direction of an order in the market.
    """
    BUY = "BUY"
    SELL = "SELL"


class OrderType(Enum):
    """
    Order type enumeration (MARKET or LIMIT).
    
    Defines the execution type of an order.
    """
    MARKET = "MARKET"
    LIMIT = "LIMIT"


class OrderStatus(Enum):
    """
    Order status enumeration.
    
    Defines the lifecycle states of an order.
    """
    NEW = "NEW"
    FILLED = "FILLED"
    CANCELED = "CANCELED"
    REJECTED = "REJECTED"


@dataclass
class Position:
    """
    Active trading position.
    
    Represents a currently held position with entry price, quantity,
    and risk management parameters (take profit, stop loss, trailing stop).
    
    @param symbol: Trading symbol (e.g., BTCUSDT)
    @param side: Order side (BUY or SELL)
    @param quantity: Position quantity
    @param entry_price: Entry price of the position
    @param timestamp: Unix timestamp of position opening
    @param take_profit_price: Take profit trigger price
    @param stop_loss_price: Stop loss trigger price
    @param trailing_active: Whether trailing stop is active
    @param trailing_stop_price: Current trailing stop price
    """
    symbol: str
    side: OrderSide
    quantity: float
    entry_price: float
    timestamp: float
    take_profit_price: float
    stop_loss_price: float
    trailing_active: bool = False
    trailing_stop_price: float = None


@dataclass
class Order:
    """
    Pending order.
    
    Represents an order that has been submitted but not yet filled.
    
    @param symbol: Trading symbol
    @param side: Order side (BUY or SELL)
    @param type: Order type (MARKET or LIMIT)
    @param quantity: Order quantity
    @param price: Limit price (None for MARKET orders)
    @param status: Current order status
    """
    symbol: str
    side: OrderSide
    type: OrderType
    quantity: float
    price: Optional[float] = None
    status: OrderStatus = OrderStatus.NEW


@dataclass
class SymbolControl:
    """
    Trading control status for a symbol.
    
    Tracks whether buying/selling is enabled for a specific symbol
    and the reason if disabled.
    
    @param buying_enabled: Whether buying is allowed for this symbol
    @param selling_enabled: Whether selling is allowed for this symbol
    @param disabled_buy_reason: Reason why buying is disabled (None if enabled)
    @param disabled_sell_reason: Reason why selling is disabled (None if enabled)
    """
    buying_enabled: bool = True
    selling_enabled: bool = True
    disabled_buy_reason: str = None
    disabled_sell_reason: str = None