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
Trading configuration module.

Contains trading parameters, capital settings, trading pairs, and risk management
parameters for the trading bot.
"""

## Capital configuration

## Initial trading capital in USDT for the bot
INITIAL_CAPITAL = 1000.0

## Trading pairs configuration

## List of cryptocurrency trading pairs in format BASEQUOTE (e.g., AVAXUSDT)
## Bot will monitor and trade these pairs according to configured parameters
TRADING_PAIRS = [
    "AVAXUSDT",
    "LINKUSDT",
    "DOTUSDT",
    "XRPUSDT",
    "ATOMUSDT"
]

## Trading parameters per symbol
##
## Dictionary mapping trading pairs to their individual strategy parameters.
## Each pair can have unique settings for position sizing, profit targets, and technical indicators.

TRADING_PARAMETERS = {

    "AVAXUSDT": {
        ## Minimum order quantity (lot size) for this trading pair
        "lot_size": 0.5,
        
        ## Maximum position size in USDT for a single entry
        "position_size": 18.0,
        
        ## Take profit target as percentage of entry price (e.g., 2.81%)
        "take_profit_percent": 2.81,
        
        ## Stop loss level as percentage below entry price (e.g., 1.41%)
        "stop_loss_percent": 1.41,
        
        ## Price movement percentage to activate trailing stop (e.g., 1.3% profit triggers trail)
        "trail_activation_percent": 1.3,
        
        ## Trailing stop distance from highest price as percentage (e.g., 0.8%)
        "trail_distance_percent": 0.8,
        
        ## Tight trailing stop distance when price approaches resistance
        "trail_tight_distance_percent": 0.5,
        
        ## Minimum 3-minute EMA200 slope to consider market trending downward (filter condition)
        "min_ema200_3m_slope": -0.008,
        
        ## Minimum 1-minute EMA20 slope for entry signal (upward trend)
        "min_ema20_1m_slope": 0.01,
        
        ## Minimum 1-minute EMA50 slope to confirm uptrend
        "min_ema50_1m_slope": 0.005,
        
        ## Volume spike coefficient - requires volume exceeding average × coefficient
        "volume_spike_coeff": 1.2,
        
        ## Maximum candle size as percentage - filters out overly large candles
        "max_candle_size": 0.8,
        
        ## Minimum distance between EMA50 and EMA200 (percentage) for trend confirmation
        "min_ema50_ema200_distance": 0.06,
        
        ## Minimum distance between EMA20 and EMA50 (percentage) for entry confirmation
        "min_ema20_ema50_distance": 0.10,
    },

    "LINKUSDT": {
        ## Minimum order quantity (lot size) for this trading pair
        "lot_size": 1,
        
        ## Maximum position size in USDT for a single entry
        "position_size": 18.0,
        
        ## Take profit target as percentage of entry price (e.g., 2.34%)
        "take_profit_percent": 2.34,
        
        ## Stop loss level as percentage below entry price (e.g., 1.12%)
        "stop_loss_percent": 1.12,
        
        ## Price movement percentage to activate trailing stop (e.g., 1.1% profit triggers trail)
        "trail_activation_percent": 1.1,
        
        ## Trailing stop distance from highest price as percentage (e.g., 0.7%)
        "trail_distance_percent": 0.7,
        
        ## Tight trailing stop distance when price approaches resistance
        "trail_tight_distance_percent": 0.45,
        
        ## Minimum 3-minute EMA200 slope to consider market trending downward (filter condition)
        "min_ema200_3m_slope": -0.008,
        
        ## Minimum 1-minute EMA20 slope for entry signal (upward trend)
        "min_ema20_1m_slope": 0.01,
        
        ## Minimum 1-minute EMA50 slope to confirm uptrend
        "min_ema50_1m_slope": 0.005,
        
        ## Volume spike coefficient - requires volume exceeding average × coefficient
        "volume_spike_coeff": 1.2,
        
        ## Maximum candle size as percentage - filters out overly large candles
        "max_candle_size": 0.8,
        
        ## Minimum distance between EMA50 and EMA200 (percentage) for trend confirmation
        "min_ema50_ema200_distance": 0.06,
        
        ## Minimum distance between EMA20 and EMA50 (percentage) for entry confirmation
        "min_ema20_ema50_distance": 0.09,
    },

    "DOTUSDT": {
        ## Minimum order quantity (lot size) for this trading pair
        "lot_size": 1.0,
        
        ## Maximum position size in USDT for a single entry
        "position_size": 18.0,
        
        ## Take profit target as percentage of entry price (e.g., 2.5%)
        "take_profit_percent": 2.5,
        
        ## Stop loss level as percentage below entry price (e.g., 1.25%)
        "stop_loss_percent": 1.25,
        
        ## Price movement percentage to activate trailing stop (e.g., 1.2% profit triggers trail)
        "trail_activation_percent": 1.2,
        
        ## Trailing stop distance from highest price as percentage (e.g., 0.75%)
        "trail_distance_percent": 0.75,
        
        ## Tight trailing stop distance when price approaches resistance
        "trail_tight_distance_percent": 0.47,
        
        ## Minimum 3-minute EMA200 slope to consider market trending downward (filter condition)
        "min_ema200_3m_slope": -0.008,
        
        ## Minimum 1-minute EMA20 slope for entry signal (upward trend)
        "min_ema20_1m_slope": 0.01,
        
        ## Minimum 1-minute EMA50 slope to confirm uptrend
        "min_ema50_1m_slope": 0.005,
        
        ## Volume spike coefficient - requires volume exceeding average × coefficient
        "volume_spike_coeff": 1.2,
        
        ## Maximum candle size as percentage - filters out overly large candles
        "max_candle_size": 0.8,
        
        ## Minimum distance between EMA50 and EMA200 (percentage) for trend confirmation
        "min_ema50_ema200_distance": 0.06,
        
        ## Minimum distance between EMA20 and EMA50 (percentage) for entry confirmation
        "min_ema20_ema50_distance": 0.08,
    },

    "XRPUSDT": {
        ## Minimum order quantity (lot size) for this trading pair
        "lot_size": 10.0,
        
        ## Maximum position size in USDT for a single entry
        "position_size": 18.0,
        
        ## Take profit target as percentage of entry price (e.g., 2.3%)
        "take_profit_percent": 2.3,
        
        ## Stop loss level as percentage below entry price (e.g., 1.15%)
        "stop_loss_percent": 1.15,
        
        ## Price movement percentage to activate trailing stop (e.g., 1.1% profit triggers trail)
        "trail_activation_percent": 1.1,
        
        ## Trailing stop distance from highest price as percentage (e.g., 0.7%)
        "trail_distance_percent": 0.7,
        
        ## Tight trailing stop distance when price approaches resistance
        "trail_tight_distance_percent": 0.45,
        
        ## Minimum 3-minute EMA200 slope to consider market trending downward (filter condition)
        "min_ema200_3m_slope": -0.008,
        
        ## Minimum 1-minute EMA20 slope for entry signal (upward trend)
        "min_ema20_1m_slope": 0.01,
        
        ## Minimum 1-minute EMA50 slope to confirm uptrend
        "min_ema50_1m_slope": 0.005,
        
        ## Volume spike coefficient - requires volume exceeding average × coefficient (higher for XRP volatility)
        "volume_spike_coeff": 1.3,
        
        ## Maximum candle size as percentage - filters out overly large candles (lower for XRP)
        "max_candle_size": 0.7,
        
        ## Minimum distance between EMA50 and EMA200 (percentage) for trend confirmation
        "min_ema50_ema200_distance": 0.05,
        
        ## Minimum distance between EMA20 and EMA50 (percentage) for entry confirmation
        "min_ema20_ema50_distance": 0.07,
    },

    "ATOMUSDT": {
        ## Minimum order quantity (lot size) for this trading pair
        "lot_size": 1.0,
        
        ## Maximum position size in USDT for a single entry
        "position_size": 18.0,
        
        ## Take profit target as percentage of entry price (e.g., 2.7%)
        "take_profit_percent": 2.7,
        
        ## Stop loss level as percentage below entry price (e.g., 1.35%)
        "stop_loss_percent": 1.35,
        
        ## Price movement percentage to activate trailing stop (e.g., 1.3% profit triggers trail)
        "trail_activation_percent": 1.3,
        
        ## Trailing stop distance from highest price as percentage (e.g., 0.8%)
        "trail_distance_percent": 0.8,
        
        ## Tight trailing stop distance when price approaches resistance
        "trail_tight_distance_percent": 0.47,
        
        ## Minimum 3-minute EMA200 slope to consider market trending downward (filter condition)
        "min_ema200_3m_slope": -0.008,
        
        ## Minimum 1-minute EMA20 slope for entry signal (upward trend)
        "min_ema20_1m_slope": 0.01,
        
        ## Minimum 1-minute EMA50 slope to confirm uptrend
        "min_ema50_1m_slope": 0.005,
        
        ## Volume spike coefficient - requires volume exceeding average × coefficient
        "volume_spike_coeff": 1.2,
        
        ## Maximum candle size as percentage - filters out overly large candles (higher for ATOM)
        "max_candle_size": 0.9,
        
        ## Minimum distance between EMA50 and EMA200 (percentage) for trend confirmation
        "min_ema50_ema200_distance": 0.07,
        
        ## Minimum distance between EMA20 and EMA50 (percentage) for entry confirmation
        "min_ema20_ema50_distance": 0.11,
    },
}

## Risk management parameters
##
## Portfolio-level and symbol-level risk limits to protect capital and prevent excessive losses.

RISK_PARAMETERS = {
    ## Maximum percentage of capital that can be exposed across all open positions (e.g., 90%)
    "max_portfolio_exposure": 90.0,
    
    ## Maximum number of consecutive losing trades before trading pauses for the symbol
    "max_consecutive_losses": 10,
    
    ## Maximum daily loss percentage per individual symbol before halting trades on that pair
    "max_daily_drawdown_per_symbol": 3.0,
    
    ## Maximum total loss percentage per symbol across all time (cumulative drawdown limit)
    "max_total_drawdown_per_symbol": 6.0,
    
    ## Maximum daily portfolio loss percentage before pausing all trading
    "max_daily_drawdown": 5.0,
    
    ## Maximum total portfolio loss percentage across all trading sessions (cumulative limit)
    "max_total_drawdown": 10.0
}
