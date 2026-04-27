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
Telegram bot module for message forwarding and TCP-Telegram server.

Provides TelegramBot class for Telegram message handling and TCP server integration.
For production server: python3 -c "from telegram.main import main; main()"
For setup (find chat_id): python3 -c "from telegram.setup import main; main()"
"""

import threading
import requests
from trading.config import config_trading
import time
from logger.logger import Logger
import logging

## Logger configuration

logger = Logger(
        logger_name='TelegramBot',
        log_file='telegram_bot.log',
        console_level=logging.INFO,
        file_level=logging.DEBUG,
        general_level=logging.DEBUG
    ).get_logger()

## Telegram Bot

class TelegramBot:
    """
    Telegram bot for sending messages and handling commands.
    
    Provides message routing to owner, command handling with inline keyboards,
    and TCP server integration for trading bot communication.
    """

    def __init__(self, bot_token: str, chat_id: str):
        """
        Initialize Telegram bot.
        
        @param bot_token: Telegram bot token for API authentication
        @param chat_id: Telegram chat ID for message routing (owner's private chat)
        """
        self.bot_token = bot_token
        self.chat_id = str(chat_id)
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self._lock = threading.RLock()
        self.available_pairs = config_trading.TRADING_PAIRS
        
    def _send_direct_message(self, message: str) -> bool:
        """
        Send message directly without queue.
        
        @param message: Message content to send
        @return: True if sent successfully, False otherwise
        """
        try:
            url = f"{self.base_url}/sendMessage"
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'HTML',
                'disable_web_page_preview': True
            }
            
            logger.debug("Sending message to Telegram")
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                logger.debug("Message sent successfully to Telegram")
                return True
            else:
                logger.error(f"Error sending to Telegram: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending to Telegram: {e}")
            return False

    def _send_symbol_selection(self, command_type: str):
        """
        Send symbol selection keyboard.
        
        @param command_type: Type of command for symbol selection
        """
        try:    
            ## Message text
            command_text = {
                "startbuying": "🛒 Enable buying for",
                "stopbuying": "⏸️ Disable buying for", 
                "startselling": "💰 Enable selling for",
                "stopselling": "⏸️ Disable selling for",
                "buy": "🛍️ Buy",
                "sell": "💵 Sell",
            }.get(command_type, "Select symbol for")
            
            ## Create keyboard with buttons
            keyboard = []

            ## Add ALL option for all commands
            keyboard.append([{
                "text": "🎯 ALL SYMBOLS",
                "callback_data": f"{command_type}:ALL"
            }])

            ## Symbols 3 per row
            row = []
            for i, symbol in enumerate(self.available_pairs, 1):
                row.append({
                    "text": symbol,
                    "callback_data": f"{command_type}:{symbol}"
                })
                
                if i % 3 == 0:
                    keyboard.append(row)
                    row = []
            
            ## Add last incomplete row
            if row:
                keyboard.append(row)
            
            ## Cancel button
            keyboard.append([{
                "text": "❌ Cancel",
                "callback_data": "cancel"
            }])
            
            ## Send message with keyboard
            url = f"{self.base_url}/sendMessage"
            payload = {
                'chat_id': self.chat_id,
                'text': f"{command_text}:",
                'reply_markup': {
                    'inline_keyboard': keyboard
                }
            }
            
            response = requests.post(url, json=payload, timeout=10)
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"❌ Error sending symbol keyboard: {e}")
            return False


    def send_message(self, message: str):
        """
        Send message asynchronously to owner.
        
        @param message: Message to send
        """
        thread = threading.Thread(target=self._send_direct_message, args=(message,), daemon=True)
        thread.start()

    def clear_pending_updates(self):
        """
        Clear all old updates to prevent UI showing immediately on startup.
        """
        try:
            url = f"{self.base_url}/getUpdates"
            ## Call getUpdates with offset parameter so Telegram forgets old updates
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("ok") and data.get("result"):
                    last_id = data["result"][-1]["update_id"]
                    ## Set offset to +1 so Telegram skips all previous updates
                    requests.get(f"{url}?offset={last_id + 1}", timeout=5)
                    logger.info("🧹 Old Telegram updates cleared.")
        except Exception as e:
            logger.error(f"❌ Error clearing Telegram updates: {e}")

    def register_bot_commands(self):
        """
        Register official command menu in Telegram.
        
        These commands appear as buttons below the input field.
        """
        url = f"{self.base_url}/setMyCommands"
        commands = [
            {"command": "getstatus", "description": "👋 Check status"},
            {"command": "getstats", "description": "📈 View statistics"},
            {"command": "starttrading", "description": "▶️ Start trading"},
            {"command": "stoptrading", "description": "⛔ Stop trading"},
            {"command": "buy", "description": "🛍️ Buy symbol"},
            {"command": "startbuying", "description": "🛒 Enable buying"},
            {"command": "stopbuying", "description": "⏸️ Disable buying"},
            {"command": "sell", "description": "💵 Sell symbol"},
            {"command": "startselling", "description": "💰 Enable selling"},
            {"command": "stopselling", "description": "⏸️ Disable selling"},
            {"command": "ping", "description": "🏓 Ping telegram bot"},
        ]

        payload = {"commands": commands}

        try:
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200 and response.json().get("ok"):
                logger.info("📋 Telegram command menu registered successfully.")
            else:
                logger.warning(f"⚠️ Failed to register commands: {response.text}")
        except Exception as e:
            logger.error(f"❌ Error registering Telegram commands: {e}")

    def handle_telegram_commands(self, server_manager):
        """
        Handle Telegram commands and show control panel with buttons.
        
        Access only for owner (verified by chat_id).
        
        @param server_manager: TCP server manager instance
        """
        logger.info("🕹️ Telegram command handler started...")

        last_update_id = 0
        url_get_updates = f"{self.base_url}/getUpdates"
        url_send_message = f"{self.base_url}/sendMessage"
        url_answer_callback = f"{self.base_url}/answerCallbackQuery"

        while True:
            try:
                response = requests.get(url_get_updates, timeout=10)
                if response.status_code != 200:
                    time.sleep(2)
                    continue

                data = response.json()
                if not data.get("ok"):
                    time.sleep(2)
                    continue

                for update in data.get("result", []):
                    update_id = update["update_id"]
                    if update_id <= last_update_id:
                        continue
                    last_update_id = update_id

                    ## Command processing
                    if "message" in update:
                        msg = update["message"]
                        chat_id = str(msg["chat"]["id"])
                        text = msg.get("text", "")

                        ## Access only for owner
                        if chat_id != self.chat_id:
                            logger.warning(f"⚠️ Rejected message from unknown chat_id: {chat_id}")
                            continue

                        if text == "/ping":
                            self.send_message("⚡ Pong!  🎯")
                            continue

                        if not server_manager.is_connected():
                            self._send_direct_message("❌ Binance bot not connected to TCP-Telegram")
                            continue

                        if text == "/getstatus":
                            server_manager.send_message("command", "getstatus")
                        elif text == "/getstats":
                            server_manager.send_message("command", "getstats")
                        elif text == "/starttrading":
                            server_manager.send_message("command", "starttrading")
                        elif text == "/stoptrading":
                            server_manager.send_message("command", "stoptrading")
                        elif text == "/startbuying":
                            self._send_symbol_selection("startbuying")
                        elif text == "/stopbuying":
                            self._send_symbol_selection("stopbuying")
                        elif text == "/startselling":
                            self._send_symbol_selection("startselling")
                        elif text == "/stopselling":
                            self._send_symbol_selection("stopselling")
                        elif text == "/buy":
                            self._send_symbol_selection("buy")
                        elif text == "/sell":
                            self._send_symbol_selection("sell")

                    elif "callback_query" in update:
                        callback = update["callback_query"]
                        chat_id = str(callback["message"]["chat"]["id"])
                        data = callback.get("data", "")
                        
                        ## Access only for owner
                        if chat_id != self.chat_id:
                            continue
                        
                        ## Answer callback (remove loading state)
                        requests.post(url_answer_callback, json={
                            'callback_query_id': callback['id']
                        })
                        
                        ## Process data
                        if data == "cancel":
                            ## Delete message with keyboard
                            requests.post(f"{self.base_url}/deleteMessage", json={
                                'chat_id': chat_id,
                                'message_id': callback['message']['message_id']
                            })
                            continue
                        
                        ## Process commands with symbols
                        if ":" in data:
                            command, symbol = data.split(":", 1)
                            
                            if command in ["startbuying", "stopbuying", "startselling", "stopselling", "buy", "sell"]:
                                ## Delete message with keyboard
                                requests.post(f"{self.base_url}/deleteMessage", json={
                                    'chat_id': chat_id,
                                    'message_id': callback['message']['message_id']
                                })
                                
                                if symbol == "ALL":
                                    server_manager.send_message("command", command)
                                else:
                                    server_manager.send_message("command", f"{command}:{symbol}")

                time.sleep(1)

            except Exception as e:
                logger.error(f"❌ Error in handle_telegram_commands: {e}")
                time.sleep(3)

    def test_connection(self) -> bool:
        """
        Test connection to Telegram.
        
        @return: True if connection successful, False otherwise
        """
        try:
            url = f"{self.base_url}/getMe"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                bot_info = response.json().get('result', {})
                logger.info(f"Telegram connected | Bot: @{bot_info.get('username','')}")
                return True
            logger.error(f"Telegram connection error: {response.status_code}")
            return False
        except Exception as e:
            logger.error(f"Telegram connection error: {e}")
            return False

    def get_chat_id_simple(self):
        """
        Simple way to get chat_id by checking recent messages.
        
        @return: Chat ID if found, None otherwise
        """
        url = f"{self.base_url}/getUpdates"
        
        print("🔍 Waiting for message from you...")
        print("IMPORTANT: First find the bot in Telegram and send it ANY message")
        print("1. Open Telegram")
        print("2. Find @{}".format(self.get_bot_username()))
        print("3. Press START or send any message")
        print("4. Wait 10 seconds...")
        print("⏹️ To stop press Ctrl+C\n")
        
        last_update_id = 0
        
        try:
            while True:
                response = requests.get(url, timeout=10)
                print(f"🔍 Checking updates... status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data['ok'] and data['result']:
                        for update in data['result']:
                            if update['update_id'] > last_update_id:
                                last_update_id = update['update_id']
                                if 'message' in update:
                                    chat_id = update['message']['chat']['id']
                                    text = update['message'].get('text', '')
                                    user_name = update['message']['chat'].get('first_name', 'Unknown')
                                    print(f"✅ Found new message!")
                                    print(f"👤 From: {user_name}")
                                    print(f"📩 Text: '{text}'")
                                    print(f"🆔 Your Chat ID: {chat_id}")
                                    print(f"💡 Add to config.py: TELEGRAM_CHAT_ID = '{chat_id}'")
                                    return chat_id
                    else:
                        print("📭 No messages found. Send bot a message in Telegram...")
                else:
                    print(f"❌ API Error: {response.status_code}")
                    
                time.sleep(2)
        except KeyboardInterrupt:
            print("\n👋 Stopping...")
            return None
        except Exception as e:
            print(f"❌ Error getting chat_id: {e}")
            return None

    def get_bot_username(self):
        """
        Get bot username.
        
        @return: Bot username or 'unknown_bot' if not found
        """
        try:
            url = f"{self.base_url}/getMe"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response.json().get('result', {}).get('username', 'unknown_bot')
        except:
            pass
        return "unknown_bot"