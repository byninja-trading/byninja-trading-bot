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
Telegram-TCP server entry point and application launcher.

Initializes Telegram bot and TCP server for bidirectional communication
between trading bot and Telegram interface. Routes TCP messages to Telegram
and processes Telegram commands back to trading bot.

Run with: python3 -c "from telegram.main import main; main()"
"""

import threading
import time
import logging

from telegram.bot_telegram import TelegramBot, logger
from telegram.config import config_telegram
from logger.logger import Logger
from tcp.server import TCPServerManager


def main():
    """
    Main entry point for TCP-Telegram server application.
    
    Performs the following operations:
    1. Validates configuration (bot token and chat ID)
    2. Initializes TelegramBot with credentials
    3. Tests connection to Telegram API
    4. Clears pending updates to avoid old messages
    5. Registers bot commands in Telegram interface
    6. Starts TCP server for trading bot integration
    7. Routes incoming TCP messages to Telegram
    8. Processes Telegram commands back to trading bot
    
    The server runs continuously until interrupted (Ctrl+C),
    then gracefully shuts down TCP server.
    
    @return: None (blocks until keyboard interrupt)
    """
    
    ## Validate configuration - check bot token
    if not hasattr(config_telegram, 'TELEGRAM_BOT_TOKEN') or not config_telegram.TELEGRAM_BOT_TOKEN:
        logger.error("❌ Please specify TELEGRAM_BOT_TOKEN in config_telegram.py")
        return
    
    ## Validate configuration - check chat ID for private access
    if not hasattr(config_telegram, 'TELEGRAM_CHAT_ID') or not config_telegram.TELEGRAM_CHAT_ID:
        logger.error("❌ Please specify TELEGRAM_CHAT_ID in config_telegram.py")
        return
    
    ## Initialize Telegram bot instance with credentials
    try:
        telegram_bot = TelegramBot(
            bot_token=config_telegram.TELEGRAM_BOT_TOKEN,
            chat_id=config_telegram.TELEGRAM_CHAT_ID
        )
        
        ## Test connection to Telegram API
        logger.info("🔍 Checking Telegram connection...")
        if not telegram_bot.test_connection():
            logger.error("❌ Failed to connect to Telegram API")
            return
        
        logger.info("✅ Telegram connected successfully")

        ## Clear old updates to prevent displaying old messages on startup
        telegram_bot.clear_pending_updates()

        ## Register bot commands for Telegram interface buttons
        telegram_bot.register_bot_commands()
    
    except Exception as e:
        logger.error(f"❌ Error initializing Telegram bot: {e}")
        return
    

    ## Handler function for processing incoming TCP messages
    def handle_tcp_message(msg_type: str, message: str):
        """
        Process incoming TCP messages and forward to Telegram.
        
        Routes messages from trading bot through Telegram to owner.
        Only processes 'message' type; ignores or warns about unknown types.
        
        @param msg_type: Type of message (expected: 'message')
        @param message: Message content to forward
        """
        if (msg_type == "message"):
            telegram_bot.send_message(message)
        else:
            logger.warning(f"⚠️ Unknown message type: {msg_type}")

    ## Create and run TCP server for trading bot integration
    try:
        ## Retrieve TCP server port from configuration
        tcp_port = getattr(config_telegram, 'TCP_SERVER_PORT')
        
        ## Create separate logger for TCP operations
        tcp_logger = Logger(
                logger_name='TelegramTCP',
                log_file='telegram_tcp.log',
                console_level=logging.DEBUG,
                file_level=logging.DEBUG,
                general_level=logging.DEBUG
            ).get_logger()

        ## Initialize TCP server with message handler
        server_manager = TCPServerManager(port=tcp_port, logger=tcp_logger, message_handler=handle_tcp_message)
        
        if server_manager.start_server():
            logger.info(f"🎯 Server ready to work on port {tcp_port}")
            logger.info("💡 All TCP messages will be forwarded to Telegram")
            
            ## Start command handler thread for processing Telegram commands
            threading.Thread(
                target=telegram_bot.handle_telegram_commands,
                args=(server_manager,),
                daemon=True
            ).start()

            ## Send startup notification
            telegram_bot.send_message("🤖 TCP-Telegram server started and ready!")
            
            ## Main event loop - wait for keyboard interrupt
            try:
                while server_manager.is_running:
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("🛑 Shutdown signal received...")
            finally:
                server_manager.stop_server()
        else:
            logger.error("❌ Failed to start TCP server")
            
    except Exception as e:
        logger.error(f"❌ Critical error: {e}")


if __name__ == "__main__":
    ## Run Telegram-TCP server application
    main()
