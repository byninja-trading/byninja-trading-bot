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
TCP logging handler module.

Provides logging handler that forwards log records to TCP manager
for remote logging capabilities.
"""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tcp.client import TCPClientManager


class TCPLogHandler(logging.Handler):
    """
    Logging handler that forwards log records to TCP manager.
    
    Sends log messages to TCP client for remote logging and monitoring
    of trading bot activity.
    """
    
    def __init__(self, tcp_manager: 'TCPClientManager') -> None:
        """
        Initialize the TCP log handler.
        
        @param tcp_manager: TCP client manager instance for sending logs
        """
        super().__init__()
        self._tcp_manager = tcp_manager

    def emit(self, record: logging.LogRecord) -> None:
        """
        Emit a log record via TCP.
        
        Formats the log record and sends it to the TCP manager
        if the log level is at INFO level or higher.
        
        @param record: Log record to emit
        """
        if record.levelno >= logging.INFO:
            self._tcp_manager.send_message("message", self.format(record))
