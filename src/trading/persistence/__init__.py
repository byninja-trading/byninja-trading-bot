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
Persistent storage module with thread-safe async persistence.

Provides PersistentMap class for dictionary-like operations with automatic
asynchronous file persistence. Uses background worker thread for non-blocking
saves with queue-based deduplication to prevent redundant writes.

Modules:
    - map: PersistentMap class with async persistence
    - models: OrderSide enum and Position dataclass
    - example: Test and demonstration functions
"""

from trading.persistence.map import PersistentMap
from trading.persistence.models import OrderSide, Position
from trading.persistence.example import main

__all__ = [
    'PersistentMap',
    'OrderSide',
    'Position',
    'main'
]