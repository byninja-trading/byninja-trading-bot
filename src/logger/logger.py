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
Logger class for configuring and managing Trading Bot logging.

This module provides a centralized logging mechanism with support for both
file and console output with configurable logging levels.
"""

import logging
import logging.handlers
from typing import Optional

from logger.formatters import get_standard_formatter


class Logger:
    """
    Logger class for configuring and managing Trading Bot logging.
    
    This class provides a centralized logging mechanism with support for both
    file and console output with configurable logging levels.
    """
    
    def __init__(
        self,
        logger_name: str,
        log_file: str,
        console_level: int,
        file_level: int,
        general_level: int
    ):
        """
        Initialize the logger.
        
        @param logger_name: Name of the logger
        @param log_file: Name of the file to save logs to
        @param console_level: Logging level for console output
        @param file_level: Logging level for file output
        @param general_level: General logging level for the logger
        """
        self._logger_name = logger_name
        self._log_file = log_file
        self._console_level = console_level
        self._file_level = file_level
        self._general_level = general_level
        
        self._logger = None
        self._setup_logger()
    
    def _setup_logger(self) -> None:
        """
        Configure logger with handlers for file and console output.
        
        Sets up both file handler (with rotation) and console handler
        with appropriate formatting and logging levels.
        """
        ## Create logger instance
        self._logger = logging.getLogger(self._logger_name)
        self._logger.setLevel(self._general_level)
        
        ## Check if logger already has handlers (to avoid duplication)
        if self._logger.handlers:
            self._logger.handlers.clear()
        
        ## Get formatter from formatters module
        formatter = get_standard_formatter()
        
        ## Handler for file output (with rotation)
        file_handler = logging.handlers.RotatingFileHandler(
            filename=self._log_file,
            maxBytes=250*1024*1024,  # 250 MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(self._file_level)
        file_handler.setFormatter(formatter)
        
        ## Handler for console output
        console_handler = logging.StreamHandler()
        console_handler.setLevel(self._console_level)
        console_handler.setFormatter(formatter)
        
        ## Add handlers to logger
        self._logger.addHandler(file_handler)
        self._logger.addHandler(console_handler)
    
    def get_logger(self) -> logging.Logger:
        """
        Get the logger object.
        
        The only public method to retrieve the configured logger instance.
        
        @return: Configured logger object
        """
        return self._logger
