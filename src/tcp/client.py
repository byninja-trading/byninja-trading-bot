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
TCP client manager module.

Manages TCP client connections with automatic reconnection logic
and message handling delegation.
"""

import time
import logging
from typing import Callable, Optional

from tcp.node import TCPNode


class TCPClientManager:
    """
    TCP client manager for handling connections and message forwarding.
    
    Manages TCP client connections with automatic reconnection logic
    and message handling delegation.
    """
    
    def __init__(self, port: int, logger: logging.Logger, message_handler: Callable[[str, str], None]):
        """
        Initialize the TCP client manager.
        
        @param port: Port number for TCP connection
        @param logger: Logger instance
        @param message_handler: Callable to handle incoming messages
        """
        self.port = port
        self.message_handler = message_handler
        self.logger = logger
        self.tcp_client: Optional[TCPNode] = None
        self.is_running = False
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 10
        self.reconnect_delay = 5
        
    def start(self) -> None:
        """
        Start the TCP client connection loop.
        
        Begins continuous connection monitoring and reconnection attempts.
        """
        self.is_running = True
        self._connect_loop()
        
    def stop(self) -> None:
        """
        Stop the TCP client.
        
        Cleanly shuts down the connection and stops reconnection attempts.
        """
        self.is_running = False
        if self.tcp_client:
            self.tcp_client.stop()
            
    def _connect_loop(self) -> None:
        """
        Infinite connection/reconnection loop.
        
        Continuously monitors connection status and attempts reconnection
        if the connection is lost.
        """
        while self.is_running:
            try:
                if self.tcp_client is None or not self.tcp_client.is_connected:
                    self._attempt_connect()
                
                ## Check connection every 30 seconds
                time.sleep(30)
                
            except Exception as e:
                self.logger.error(f"❌ Error in TCP connection loop: {e}")
                time.sleep(self.reconnect_delay)
    
    def _attempt_connect(self) -> bool:
        """
        Attempt to connect with exponential backoff delay.
        
        Uses exponential backoff strategy to avoid overwhelming the server
        during connection failures.
        
        @return: True if connection successful, False otherwise
        """
        try:
            if self.reconnect_attempts > 0:
                delay = min(self.reconnect_delay * (2 ** self.reconnect_attempts), 300)  # max 5 minutes
                self.logger.info(f"🔄 Attempting TCP reconnection in {delay}s (attempt {self.reconnect_attempts})")
                time.sleep(delay)
            
            self.logger.info("🔄 Connecting to TCP server...")
            
            ## Create new client
            if self.tcp_client:
                self.tcp_client.stop()
                
            self.tcp_client = TCPNode(self.port, self.logger)
            ## Set message handler
            self.tcp_client.set_message_handler(self._handle_tcp_message)
            
            if self.tcp_client.connect(timeout=10.0):
                self.reconnect_attempts = 0
                self.logger.info("✅ TCP client connected successfully")
                return True
            else:
                self.reconnect_attempts += 1
                self.logger.warning(f"❌ Failed to connect to TCP (attempt {self.reconnect_attempts})")
                return False
                
        except Exception as e:
            self.reconnect_attempts += 1
            self.logger.error(f"❌ TCP connection error: {e}")
            return False
    
    def _handle_tcp_message(self, msg_type: str, message: str) -> None:
        """
        Handle incoming TCP messages and forward to message handler.
        
        @param msg_type: Type of the message
        @param message: Message content
        """
        try:
            self.logger.debug(f"📨 Received TCP message: {msg_type} - {message}")
                
            ## Forward to message handler
            if self.message_handler:
                self.message_handler(msg_type, message)

            self.logger.debug("✅ Message processed")
        except Exception as e:
            self.logger.error(f"❌ Error processing TCP message: {e}")

    def is_connected(self) -> bool:
        """
        Check if TCP client is connected.
        
        @return: True if connected, False otherwise
        """
        return self.tcp_client and self.tcp_client.is_connected
    
    def send_message(self, msg_type: str, message: str) -> bool:
        """
        Send message with automatic reconnection on error.
        
        @param msg_type: Type of the message
        @param message: Message content
        @return: True if sent successfully, False otherwise
        """
        if not self.is_connected():
            self.logger.debug("TCP not connected, skipping message")
            return False

        try:
            self.tcp_client.send_message(msg_type, message)
            return True
        except Exception as e:
            self.logger.warning(f"❌ Error sending via TCP, reconnecting: {e}")
            self.reconnect_attempts += 1
            self.tcp_client = None
            return False
