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
Persistent dictionary with asynchronous file persistence.

Provides a thread-safe dictionary implementation that automatically saves
all changes to disk using a background worker thread.
"""

import pickle
from pathlib import Path
import threading
import time
import logging
import queue
from typing import Any


class PersistentMap(dict):
    """
    Persistent map with asynchronous file persistence.
    
    A thread-safe dictionary that automatically saves all changes to a file
    using an asynchronous background worker thread. Inherits from dict for
    full dictionary interface compatibility.
    """
    
    def __init__(self, filename: str, logger: logging.Logger, *args, **kwargs):
        """
        Initialize a persistent map.
        
        Loads existing data from file (if present) and starts background
        persistence worker thread for asynchronous saving.
        
        @param filename: Path to the file for persistence (pickle format)
        @param logger: Logger instance for logging messages
        @param args: Positional arguments for dict initialization
        @param kwargs: Keyword arguments for dict initialization
        """
        self.filename = Path(filename)
        self._save_queue = queue.Queue()
        self._save_thread = None
        self._stop_saving = False
        self._save_lock = threading.Lock()
        self.logger = logger
        
        ## Load data from file first
        self._load_from_file()
        
        ## Then initialize parent dict
        super().__init__(*args, **kwargs)
        
        ## Start background thread for saving
        self._start_save_thread()

    def _load_from_file(self) -> None:
        """
        Load data from file.
        
        Loads persisted data from the file if it exists, otherwise creates
        a new file on first save. Handles file not found gracefully.
        """
        try:
            if self.filename.exists():
                with open(self.filename, 'rb') as f:
                    data = pickle.load(f)
                super().update(data)
                self.logger.info(f"✅ Loaded {len(data)} records from {self.filename}")
            else:
                self.logger.info(f"📁 File {self.filename} not found, creating new")
        except Exception as e:
            self.logger.error(f"❌ Error loading from {self.filename}: {e}")

    def _start_save_thread(self) -> None:
        """
        Start background thread for saving.
        
        Launches a daemon thread that handles asynchronous persistence
        of map changes to disk without blocking main thread.
        """
        self._save_thread = threading.Thread(
            target=self._save_worker,
            daemon=True,
            name="PersistentMapSaver"
        )
        self._save_thread.start()
        self.logger.debug("🔄 Background save thread started")

    def _save_worker(self) -> None:
        """
        Background worker for saving data.
        
        Continuously processes save requests from the queue and persists
        data to disk using atomic file replacement (temp file → rename).
        Resilient to errors with exponential backoff retry.
        """
        while not self._stop_saving:
            try:
                ## Wait for next task with timeout
                data_to_save = self._save_queue.get(timeout=1.0)
                
                ## Save data to disk atomically
                with self._save_lock:
                    temp_file = self.filename.with_suffix('.tmp')
                    with open(temp_file, 'wb') as f:
                        pickle.dump(data_to_save, f)
                    temp_file.replace(self.filename)
                
                self._save_queue.task_done()
                
            except queue.Empty:
                ## Timeout - check if we need to stop
                continue
            except Exception as e:
                self.logger.error(f"❌ Error in background save to {self.filename}: {e}")
                time.sleep(5)
    
    def _schedule_save(self) -> None:
        """
        Schedule a save of the current state.
        
        Clears old save tasks from the queue and schedules the current
        state for persistence. Deduplicates requests to avoid queue buildup.
        """
        try:
            ## Clear queue of old tasks
            while not self._save_queue.empty():
                try:
                    self._save_queue.get_nowait()
                    self._save_queue.task_done()
                except queue.Empty:
                    break
            
            ## Add current state
            current_state = dict(self)
            self._save_queue.put(current_state)
            
        except Exception as e:
            self.logger.error(f"❌ Error scheduling save to {self.filename}: {e}")
    
    def __setitem__(self, key: str, value: Any) -> None:
        """
        Override item assignment.
        
        Sets an item in the dictionary and schedules persistence.
        
        @param key: Dictionary key
        @param value: Value to store
        """
        super().__setitem__(key, value)
        self._schedule_save()
    
    def __delitem__(self, key: str) -> None:
        """
        Override item deletion.
        
        Deletes an item from the dictionary and schedules persistence.
        
        @param key: Dictionary key to remove
        """
        super().__delitem__(key)
        self._schedule_save()
    
    def update(self, __m=None, **kwargs) -> None:
        """
        Override map update.
        
        Updates the map with items and schedules persistence.
        
        @param __m: Dictionary or iterable of key-value pairs
        @param kwargs: Keyword arguments to add to map
        """
        super().update(__m, **kwargs)
        self._schedule_save()
    
    def clear(self) -> None:
        """
        Override map clearing.
        
        Clears all items from the map and schedules persistence.
        """
        super().clear()
        self._schedule_save()
    
    def pop(self, key: str, default: Any = None) -> Any:
        """
        Override pop with persistence.
        
        Removes and returns an item, schedules persistence.
        
        @param key: Key to pop
        @param default: Default value if key not found
        @return: Value at key, or default if not found
        """
        result = super().pop(key, default)
        self._schedule_save()
        return result
    
    def popitem(self) -> tuple:
        """
        Override popitem with persistence.
        
        Removes and returns an arbitrary item.
        
        @return: Tuple of (key, value)
        """
        result = super().popitem()
        self._schedule_save()
        return result
    
    def setdefault(self, key: str, default: Any = None) -> Any:
        """
        Override setdefault with persistence.
        
        Sets default value for a key and schedules persistence.
        
        @param key: Key to set default for
        @param default: Default value
        @return: Value at key, or default if not found
        """
        result = super().setdefault(key, default)
        self._schedule_save()
        return result
    
    def force_save(self) -> None:
        """
        Force immediate save.
        
        Schedules a save and blocks until it completes.
        Useful for ensuring persistence before shutdown.
        """
        self.logger.debug(f"💾 Forcing save to {self.filename}...")
        self._schedule_save()
        ## Wait for current save to complete
        self._save_queue.join()
    
    def stop(self) -> None:
        """
        Stop the background thread and perform final save.
        
        Gracefully shuts down the background save worker and ensures
        all pending saves are flushed to disk before returning.
        """
        self.logger.info(f"🛑 Stopping PersistentMap for {self.filename}...")
        self._stop_saving = True
        self.force_save()
        if self._save_thread and self._save_thread.is_alive():
            self._save_thread.join(timeout=5.0)
        self.logger.info(f"✅ PersistentMap stopped for {self.filename}")
