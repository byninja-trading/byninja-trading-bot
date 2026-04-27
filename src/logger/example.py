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
Logger usage example and demonstration.

This module demonstrates how to configure and use the Logger class
for centralized logging with both file and console output.
"""

import logging
from logger.logger import Logger


def main():
    """
    Example of using the Logger class.
    
    Demonstrates initialization and usage of the Logger class with
    different logging levels and output channels. Creates a logger instance,
    configures it for both file and console output, and logs messages at
    various severity levels.
    """
    
    ## Create logger with required parameters
    ## - logger_name: Identifier for this logger instance
    ## - log_file: Output file path for persistent logging
    ## - console_level: Minimum level for console output (INFO)
    ## - file_level: Minimum level for file output (DEBUG - captures everything)
    ## - general_level: Overall logger level (DEBUG - most verbose)
    bot_logger = Logger(
        logger_name='TradingBot',
        log_file='example.log',
        console_level=logging.INFO,
        file_level=logging.DEBUG,
        general_level=logging.DEBUG
    )
    
    ## Get logger through the public method
    logger = bot_logger.get_logger()
    
    ## Test different logging levels
    logger.debug("🔍 DEBUG message - detailed diagnostic information")
    logger.info("ℹ️  INFO message - general informational message")
    logger.warning("⚠️  WARNING message - something unexpected occurred")
    logger.error("❌ ERROR message - serious problem occurred")
    logger.critical("🚨 CRITICAL message - critical error, immediate action needed")
    
    print("\n" + "="*60)
    print("✅ Logger example completed successfully")
    print("Check 'example.log' for file output with DEBUG level messages")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
