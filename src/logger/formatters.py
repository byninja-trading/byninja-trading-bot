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
Custom logging formatters for the trading bot.

Provides various formatter implementations for different logging contexts
and output channels (console, file, etc.).
"""

import logging


class StandardFormatter(logging.Formatter):
    """
    Standard formatter for log messages.
    
    Formats log messages with timestamp, logger name, level, and message content.
    """
    
    def __init__(self):
        """
        Initialize the standard formatter.
        
        Sets up the format string with standard log information.
        """
        super().__init__(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )


def get_standard_formatter() -> logging.Formatter:
    """
    Get a standard formatter instance.
    
    @return: StandardFormatter instance for logging
    """
    return StandardFormatter()
