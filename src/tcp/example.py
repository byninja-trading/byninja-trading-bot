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
TCP node example and usage demonstration.

Demonstrates TCP client-server communication with automatic reconnection,
message handling, and multi-threaded operation.

Run with: python3 -m tcp.example
"""

import logging
import time
import threading
import random
from typing import Callable

from tcp.node import TCPNode


def main() -> None:
    """
    Example TCP node usage with server and client operation.
    
    Demonstrates both server (continuously listening) and client
    (with periodic reconnection) modes with bidirectional communication.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger("TCPApp")
    
    PORT = 8888
    
    def server_message_handler(tag: str, message: str) -> None:
        """
        Handle incoming server messages.
        
        @param tag: Message tag/type
        @param message: Message content
        """
        logger.debug(f"🖥️ Server received: [{tag}] {message}")
        
        ## Send response to client
        if hasattr(server_message_handler, 'server'):
            server_message_handler.server.send_message("response", f"Response to: {message}")
    
    def client_message_handler(tag: str, message: str) -> None:
        """
        Handle incoming client messages.
        
        @param tag: Message tag/type
        @param message: Message content
        """
        logger.debug(f"📱 Client received: [{tag}] {message}")

    def run_server() -> None:
        """
        Run TCP server.
        
        Continuously listens for client connections and handles
        bidirectional message communication.
        """
        server = TCPNode(PORT, logger)
        server.set_message_handler(server_message_handler)
        server_message_handler.server = server  ## Store reference for responses
        
        if server.start_server():
            logger.info("🎯 Server started and ready to accept clients")
            
            try:
                ## Server runs indefinitely
                while True:
                    ## Wait for connection
                    if server.wait_for_connection(timeout=5.0):
                        logger.info("🎉 New connection established!")
                        
                        ## Send welcome message
                        server.send_message("welcome", "Welcome to the server!")
                        
                        ## Periodically send status
                        message_count = 0
                        while server.is_connected:
                            server.send_message("status", f"Server running normally. Messages: {message_count}")
                            message_count += 1
                            time.sleep(3)
                    
                    ## Small pause before next wait
                    time.sleep(1)
                    
            except KeyboardInterrupt:
                logger.info("🛑 Server shutdown signal received")
            finally:
                server.stop()
        else:
            logger.error("❌ Failed to start server")

    def run_client() -> None:
        """
        Run TCP client with automatic reconnection.
        
        Periodically connects to server, simulates work, and reconnects
        with random intervals to demonstrate resilience.
        """
        client_id = 1
        
        while True:
            logger.info(f"🔄 Starting client #{client_id}")
            
            client = TCPNode(PORT, logger)
            client.set_message_handler(client_message_handler)
            
            if client.connect(timeout=5.0):
                logger.info(f"✅ Client #{client_id} successfully connected")
                
                ## Simulate client operation
                try:
                    work_duration = random.randint(5, 15)  ## Work time 5-15 seconds
                    start_time = time.time()
                    
                    while time.time() - start_time < work_duration and client.is_connected:
                        ## Send data to server
                        message = f"Hello from client #{client_id}! Time: {time.time()}"
                        client.send_message("data", message)
                        
                        ## Simulate work
                        time.sleep(2)
                        
                        ## Occasionally simulate crash
                        if random.random() < 0.1:  ## 10% chance
                            logger.warning(f"💥 Client #{client_id} crashed!")
                            break
                    
                except Exception as e:
                    logger.error(f"❌ Error in client #{client_id}: {e}")
                
                ## Proper disconnection
                logger.info(f"🔌 Client #{client_id} shutting down")
                client.stop()
                
            else:
                logger.error(f"❌ Client #{client_id} failed to connect")
            
            ## Wait before next restart
            wait_time = random.randint(3, 8)
            logger.info(f"⏰ Waiting {wait_time}s before next client...")
            time.sleep(wait_time)
            
            client_id += 1

    ## Start server and client in separate threads
    server_thread = threading.Thread(target=run_server, daemon=True, name="ServerThread")
    client_thread = threading.Thread(target=run_client, daemon=True, name="ClientThread")
    
    server_thread.start()
    time.sleep(1)  ## Give server time to start
    client_thread.start()
    
    ## Wait for completion (or Ctrl+C)
    try:
        server_thread.join()
        client_thread.join()
    except KeyboardInterrupt:
        logger.info("👋 Application shutting down")


if __name__ == "__main__":
    main()
