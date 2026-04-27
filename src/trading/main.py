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
ByNinja Trading Bot main entry point.

Provides the main() function for starting the ByNinja crypto trading bot
with signal handling and graceful shutdown.

Run with: python3 -c "from trading.main import main; main()"
"""

import time
import signal
import threading
import logging
from typing import Optional

from trading.bot_trading import ByNinjaTradingBot, BOT_VERSION, logger
from trading.config import config_binance
from logger.logger import Logger
from tcp.client import TCPClientManager
from tcp.handlers import TCPLogHandler


def tcp_client_integration(trading_bot: 'ByNinjaTradingBot') -> Optional[TCPClientManager]:
    """
    Initialize and start TCP client integration.
    
    Sets up TCP server for remote command handling and routes commands
    to appropriate bot methods.
    
    @param trading_bot: Bot instance for command execution
    @return: TCP manager instance or None if error
    """
    try:
        logger.info("🔄 Starting TCP client")
        
        tcp_logger = Logger(
                logger_name='TradingTCP',
                log_file='trading_tcp.log',
                console_level=logging.INFO,
                file_level=logging.DEBUG,
                general_level=logging.DEBUG
            ).get_logger()

        def handle_tcp_message(msg_type: str, message: str):
            """
            Handler for incoming TCP messages.
            
            @param msg_type: Type of message
            @param message: Message content
            """
            if (msg_type == "command" and message == "starttrading"):
                trading_bot.start_trading()
            elif (msg_type == "command" and message == "stoptrading"):
                trading_bot.stop_trading()
            elif (msg_type == "command" and message == "getstatus"):
                if trading_bot.is_running:
                    trading_bot.log_system_status()
                else:
                    logger.warning("⚠️  Bot stopped.")
            elif (msg_type == "command" and message == "getstats"):
                trading_bot.risk_manager.log_statistics()
            elif (msg_type == "command" and message == "startbuying"):
                trading_bot.enable_buying()
            elif (msg_type == "command" and message == "stopbuying"):
                trading_bot.disable_buying()
            elif (msg_type == "command" and message == "startselling"):
                trading_bot.enable_selling()
            elif (msg_type == "command" and message == "stopselling"):
                trading_bot.disable_selling()
            elif (msg_type == "command" and message == "sell"):
                trading_bot.force_sell()
            elif (msg_type == "command" and message == "buy"):
                trading_bot.force_buy()
            elif msg_type == "command" and message.startswith("startbuying:"):
                symbol = message.split(":")[1]
                trading_bot.enable_buying(symbol)
            elif msg_type == "command" and message.startswith("stopbuying:"):
                symbol = message.split(":")[1]
                trading_bot.disable_buying(symbol)
            elif msg_type == "command" and message.startswith("startselling:"):
                symbol = message.split(":")[1]
                trading_bot.enable_selling(symbol)
            elif msg_type == "command" and message.startswith("stopselling:"):
                symbol = message.split(":")[1]
                trading_bot.disable_selling(symbol)
            elif msg_type == "command" and message.startswith("sell:"):
                symbol = message.split(":")[1]
                trading_bot.force_sell(symbol)
            elif msg_type == "command" and message.startswith("buy:"):
                symbol = message.split(":")[1]
                trading_bot.force_buy(symbol)
            else:
                logger.warning(f"⚠️  Unknown message type | msg_type: {msg_type} message: {message}")

        tcp_port = getattr(config_binance, 'TCP_SERVER_PORT')

        tcp_manager = TCPClientManager(port=tcp_port, logger=tcp_logger, message_handler=handle_tcp_message)

        tcp_thread = threading.Thread(target=tcp_manager.start, daemon=True)

        tcp_handler = TCPLogHandler(tcp_manager)
        tcp_handler.setLevel(logging.INFO)
        tcp_handler.setFormatter(logging.Formatter('%(message)s'))
        logger.addHandler(tcp_handler)

        tcp_thread.start()
        time.sleep(1)

        return tcp_manager

    except Exception as e:
        logger.error(f"❌ Error starting TCP client: {e}")
        return None


def main():
    """
    Main entry point for the professional crypto trading bot.
    
    Initializes the bot, sets up signal handling, and starts trading.
    """
    import threading
    
    logger.debug(f"🥷 BYNINJA TRADING BOT v{BOT_VERSION}")
    logger.debug("=" * 60)
    
    try:
        trading_bot = ByNinjaTradingBot()
        
        tcp_manager = tcp_client_integration(trading_bot)

        def signal_handler(sig, frame):
            logger.debug("🛑 Shutdown signal received...")
            trading_bot.stop_trading()
            time.sleep(1)
            tcp_manager.stop()
            exit(0)
            
        signal.signal(signal.SIGINT, signal_handler)
        
        trading_bot.start_trading()
        
        logger.debug("💡 Bot active. Press Ctrl+C to stop.")
        
        while True:
            time.sleep(1)
            
    except Exception as e:
        logger.error(f"❌ Critical error: {e}")


if __name__ == "__main__":
    main()