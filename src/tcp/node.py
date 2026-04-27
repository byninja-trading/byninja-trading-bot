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

import socket
import threading
import json
import logging
import time
import queue
import random
from typing import Callable, Optional

class TCPNode:
    """
    TCP node for client-server communication.
    
    Supports both server and client modes with asynchronous message sending/receiving
    and automatic thread management.
    """
    
    def __init__(self, port: int, logger: logging.Logger, host: str = 'localhost'):
        """
        Initialize a TCP node.
        
        @param port: Port number to listen on or connect to
        @param logger: Logger instance for logging events
        @param host: Host address (default: localhost)
        """
        self.port = port
        self.host = host
        self.logger = logger
        self.socket = None
        self.connection = None
        self.peer_address = None
        
        self.is_running = False
        self.is_connected = False
        self.mode = None  ## 'server' or 'client'
        
        self.message_handler: Optional[Callable[[str, str], None]] = None
        self.receive_thread = None
        self.server_thread = None
        
        ## Queues for synchronization
        self.send_queue = queue.Queue()
        self.connection_event = threading.Event()
        self.send_thread = None
        
    def start_server(self) -> bool:
        """
        Start node in server mode.
        
        @return: True if started successfully, False otherwise
        """
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            self.socket.listen(1)
            self.is_running = True
            self.mode = 'server'
            
            self.server_thread = threading.Thread(target=self._accept_connections, daemon=True)
            self.server_thread.start()
            
            self.send_thread = threading.Thread(target=self._send_worker, daemon=True)
            self.send_thread.start()
            
            self.logger.info(f"🚀 Server started on {self.host}:{self.port}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting server: {e}")
            return False
    
    def connect(self, timeout: float = 10.0) -> bool:
        """
        Connect to server.
        
        @param timeout: Connection timeout in seconds
        @return: True if connected successfully, False otherwise
        """
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(timeout)
            self.socket.connect((self.host, self.port))
            self.connection = self.socket
            self.is_connected = True
            self.is_running = True
            self.mode = 'client'
            self.connection_event.set()
            
            self.receive_thread = threading.Thread(target=self._receive_messages, daemon=True)
            self.receive_thread.start()
            
            self.send_thread = threading.Thread(target=self._send_worker, daemon=True)
            self.send_thread.start()
            
            self.logger.info(f"✅ Connected to server {self.host}:{self.port}")
            return True
            
        except socket.timeout:
            self.logger.error(f"Connection timeout to {self.host}:{self.port}")
            return False
        except Exception as e:
            self.logger.error(f"Connection error: {e}")
            return False
    
    def wait_for_connection(self, timeout: Optional[float] = None) -> bool:
        """
        Wait for client connection (server mode only).
        
        @param timeout: Maximum time to wait in seconds
        @return: True if connection established, False if timeout
        """
        if self.mode != 'server':
            self.logger.warning("This method is only for server mode")
            return self.is_connected
            
        self.logger.info("Waiting for client connection...")
        return self.connection_event.wait(timeout)
    
    def _accept_connections(self):
        """
        Accept incoming connections (continuously waits for new connections).
        """
        while self.is_running:
            try:
                self.logger.info("🔍 Waiting for client connection...")
                self.connection, self.peer_address = self.socket.accept()
                self.is_connected = True
                self.connection_event.set()
                
                self.logger.info(f"🔗 Client connected: {self.peer_address}")
                
                ## Start thread for receiving messages
                self.receive_thread = threading.Thread(target=self._receive_messages, daemon=True)
                self.receive_thread.start()
                
                ## Wait for current connection to be closed
                self.receive_thread.join()
                
                ## Prepare for next connection
                self._cleanup_connection()
                self.logger.info("🔄 Ready for next connection")
                
            except Exception as e:
                if self.is_running:
                    self.logger.error(f"Error accepting connection: {e}")
                    break
    
    def _receive_messages(self):
        """
        Receive messages from connected node.
        """

        self.connection.settimeout(1.0)  ## 1 second timeout

        while self.is_connected:
            try:
                header = self.connection.recv(4)
                if not header:
                    self.logger.warning("🔌 Connection closed by client")
                    break
                    
                message_length = int.from_bytes(header, byteorder='big')
                
                chunks = []
                bytes_received = 0
                while bytes_received < message_length:
                    chunk = self.connection.recv(min(message_length - bytes_received, 4096))
                    if not chunk:
                        break
                    chunks.append(chunk)
                    bytes_received += len(chunk)
                    
                if bytes_received != message_length:
                    self.logger.error("Failed to receive complete message")
                    continue
                    
                json_data = b''.join(chunks).decode('utf-8')
                data = json.loads(json_data)
                
                tag = data.get('tag', '')
                message = data.get('message', '')
            
                if self.message_handler:
                    self.message_handler(tag, message)
                    
            except socket.timeout:
                continue
            except Exception as e:
                if self.is_connected:
                    self.logger.error(f"Error receiving message: {e}")
                break
        
        self._handle_disconnection()
    
    def _send_worker(self):
        """
        Background worker thread for sending messages.
        """
        while self.is_running or self.is_connected:
            try:
                tag, message = self.send_queue.get(timeout=1.0)
                
                if not self.is_connected:
                    self.logger.warning("Not connected, message not sent")
                    continue
                
                data = {
                    'tag': tag,
                    'message': message,
                    'timestamp': time.time()
                }
                
                json_data = json.dumps(data).encode('utf-8')
                header = len(json_data).to_bytes(4, byteorder='big')
                self.connection.send(header + json_data)
                
                self.logger.debug(f"📤 Sent: [{tag}] {message}")
                
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Send error: {e}")
    
    def send_message(self, tag: str, message: str):
        """
        Send a message.
        
        @param tag: Message tag/type
        @param message: Message content
        """
        self.send_queue.put((tag, message))
    
    def set_message_handler(self, handler: Callable[[str, str], None]):
        """
        Set message handler callback.
        
        @param handler: Callable that receives (tag, message) arguments
        """
        self.message_handler = handler
    
    def _cleanup_connection(self):
        """
        Clean up after connection closure.
        """
        if self.connection:
            self.connection.close()
            self.connection = None
        self.is_connected = False
        self.connection_event.clear()
    
    def _handle_disconnection(self):
        """
        Handle connection closure.
        """
        self.logger.info("🔌 Client disconnected")
        self._cleanup_connection()
    
    def stop(self):
        """
        Stop the node.
        """
        self.is_running = False
        self.is_connected = False
        self.connection_event.set()
        
        if self.connection:
            self.connection.close()
        if self.socket:
            self.socket.close()
        
        self.logger.info("⏹️ Node stopped")