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
Telegram bot setup and configuration utility.

Utility for discovering and validating Telegram chat ID for private bot access.
Use this to configure TELEGRAM_CHAT_ID in config_telegram.py.

Run with: python3 -c "from telegram.setup import main; main()"
"""

import time
from telegram.bot_telegram import TelegramBot
from telegram.config import config_telegram


def main():
    """
    Interactive setup utility for finding Telegram chat ID.
    
    Guides user through finding their private chat ID by:
    1. Verifying bot token configuration
    2. Testing Telegram API connection
    3. Waiting for user to send message to bot
    4. Extracting and validating chat ID
    5. Testing message sending capability
    
    Displays chat ID and instructions for updating configuration.
    """
    
    print("⚠️  Telegram Bot Setup - Find Your Chat ID\n")
    
    ## Verify bot token exists in configuration
    if not hasattr(config_telegram, 'TELEGRAM_BOT_TOKEN') or not config_telegram.TELEGRAM_BOT_TOKEN:
        print("❌ Please specify TELEGRAM_BOT_TOKEN in config_telegram.py")
        print("📖 Get token from @BotFather in Telegram")
        return
    
    ## Create bot instance for setup
    bot = TelegramBot(
        bot_token=config_telegram.TELEGRAM_BOT_TOKEN,
        chat_id=""  ## Will be determined from incoming message
    )
    
    ## Verify connection to Telegram API
    print("🔍 Checking Telegram API connection...")
    if not bot.test_connection():
        print("❌ Failed to connect to Telegram API")
        print("💡 Verify token correctness and internet connection")
        return
    
    ## Guide user through chat ID discovery
    print("\n🎯 Finding Chat ID...")
    print("=" * 60)
    
    chat_id = bot.get_chat_id_simple()
    
    if chat_id:
        print(f"\n✅ Chat ID obtained successfully!")
        print(f"🆔 Your Chat ID: {chat_id}")
        print(f"\n💾 Add this to config_telegram.py:")
        print(f'TELEGRAM_CHAT_ID = "{chat_id}"\n')
        
        ## Test message sending with discovered chat ID
        print("🧪 Testing message sending capability...")
        test_bot = TelegramBot(
            bot_token=config_telegram.TELEGRAM_BOT_TOKEN,
            chat_id=chat_id
        )
        
        ## Wait before sending test message
        time.sleep(2)
        
        ## Send test message synchronously for immediate feedback
        success = test_bot._send_direct_message("✅ Test message! Chat ID works correctly!")
        
        if success:
            print("🎉 Test message sent! Check Telegram.")
        else:
            print("❌ Failed to send test message")
    else:
        print("\n❌ Failed to get Chat ID")
        print("💡 Make sure you sent a message to the bot in Telegram")


if __name__ == "__main__":
    ## Run interactive setup
    main()
