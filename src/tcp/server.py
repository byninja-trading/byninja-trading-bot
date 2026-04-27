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
TCP server manager module.

Manages TCP server operations and forwards incoming messages to handlers.
"""

import threading
import logging
from typing import Callable, Optional

from tcp.node import TCPNode


class TCPServerManager:
    """
    TCP server manager for handling incoming connections and message forwarding.
    
    Manages TCP server operations and forwards incoming messages to registered
    message handler callbacks.
    """
    
    def __init__(self, port: int, logger: logging.Logger, message_handler: Callable[[str, str], None]):
        """
        Initialize the TCP server manager.
        
        @param port: Port number for TCP server
        @param logger: Logger instance
        @param message_handler: Callable to handle incoming messages
        """
        self.port = port
        self.message_handler = message_handler
        self.tcp_server: Optional[TCPNode] = None
        self.is_running = False
        self.logger = logger
    
    def start_server(self) -> bool:
        """
        Start the TCP server.
        
        Initializes the TCP server on the specified port and starts
        listening for incoming client connections in a separate thread.
        
        @return: True if started successfully, False otherwise
        """
        try:
            self.tcp_server = TCPNode(self.port, self.logger)
            self.is_running = True
            
            ## Set message handler
            self.tcp_server.set_message_handler(self._handle_tcp_message)
            
            ## Start server in separate thread
            server_thread = threading.Thread(target=self._run_server, daemon=True)
            server_thread.start()
            
            self.logger.info(f"🚀 TCP server started on port {self.port}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error starting TCP server: {e}")
            return False
    
    def is_connected(self) -> bool:
        """
        Check if TCP server is running and has active connections.
        
        @return: True if connected, False otherwise
        """
        return self.tcp_server and self.tcp_server.is_connected

    def _run_server(self) -> None:
        """
        Run server in separate thread.
        
        Executes the server's main loop which continuously listens for
        incoming client connections.
        """
        try:
            self.tcp_server.start_server()
        except Exception as e:
            self.logger.error(f"❌ Error in TCP server operation: {e}")
    
    def _handle_tcp_message(self, msg_type: str, message: str) -> None:
        """
        Handle incoming TCP messages and forward to registered handler.
        
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
    
    def send_message(self, msg_type: str, message: str) -> bool:
        """
        Send message to connected client.
        
        @param msg_type: Type of the message
        @param message: Message content
        @return: True if sent successfully, False otherwise
        """
        if not self.is_connected():
            self.logger.debug("TCP not connected, skipping message")
            return False

        try:
            self.tcp_server.send_message(msg_type, message)
            return True
        except Exception as e:
            self.logger.warning(f"❌ Error sending via TCP: {e}")
            return False

    def stop_server(self) -> None:
        """
        Stop the TCP server.
        
        Gracefully shuts down the server and closes all active connections.
        """
        self.is_running = False
        if self.tcp_server:
            self.tcp_server.stop()
        self.logger.info("🛑 TCP server stopped")
