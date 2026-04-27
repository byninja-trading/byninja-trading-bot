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
Persistent map testing and example usage.

Demonstrates initialization, persistence, asynchronous saving, and data integrity
of the PersistentMap with complex object serialization.

Run with: python3 -c "from trading.persistence.example import main; main()"
"""

import time
import random
import logging

from trading.persistence.map import PersistentMap
from trading.persistence.models import Position, OrderSide


def main():
    """
    Main test function for persistent map functionality.
    
    Tests the following scenarios:
    1. Map creation and data loading from file
    2. Adding and removing items with automatic persistence
    3. Asynchronous saving with deduplication
    4. Force save synchronization
    5. Data integrity verification after reload
    
    Displays progress with emoji indicators and timing information.
    """
    
    print("🧪 Testing PersistentMap with asynchronous persistence\n")
    
    ## Configure logger for persistent map operations
    logger = logging.getLogger('PersistentMap')
    logger.setLevel(logging.DEBUG)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    logger.addHandler(console_handler)

    ## Create persistent map instance
    pm = PersistentMap("test_positions.pkl", logger)
    
    ## Test 1: Add initial test data
    print("📝 Adding test positions...")
    pm["BTCUSDT"] = Position(
        symbol="BTCUSDT",
        quantity=0.1,
        entry_price=50000.0,
        side=OrderSide.BUY
    )
    
    pm["ETHUSDT"] = Position(
        symbol="ETHUSDT", 
        quantity=1.5,
        entry_price=3500.0,
        side=OrderSide.BUY
    )
    
    print(f"📊 Current state: {len(pm)} positions")
    for key, value in pm.items():
        print(f"   - {key}: {value}")
    
    time.sleep(1.0)

    ## Test 2: Loading after initial write
    print("\n🔄 Testing loading after initial write...")
    pm_loaded1 = PersistentMap("test_positions.pkl", logger)
    print(f"📊 Loaded from file: {len(pm_loaded1)} positions")
    for key, value in pm_loaded1.items():
        print(f"   - {key}: {value}")

    ## Test 3: Intensive changes to demonstrate asynchronicity
    print("\n🔄 Intensive changes (adding and removing)...")
    existing_keys = list(pm.keys())
    
    for i in range(10):
        ## Randomly choose add or remove operation
        if random.random() > 0.3 and len(existing_keys) > 2:
            ## 70% chance to remove existing key
            key_to_remove = random.choice(existing_keys)
            del pm[key_to_remove]
            existing_keys.remove(key_to_remove)
            print(f"   ➖ Removed {key_to_remove}")
        else:
            ## Add new position
            new_symbol = f"TEST{i}"
            pm[new_symbol] = Position(
                symbol=new_symbol,
                quantity=random.uniform(0.1, 1.0),
                entry_price=random.uniform(100, 1000),
                side=OrderSide.BUY if random.random() > 0.5 else OrderSide.SELL
            )
            existing_keys.append(new_symbol)
            print(f"   ➕ Added {new_symbol}")
        
        time.sleep(0.1)  ## Rapid changes to test queue deduplication
    
    print(f"\n📊 Final state after cycle: {len(pm)} positions")
    for key, value in pm.items():
        print(f"   - {key}: {value}")
    
    ## Test 4: Force save with blocking
    print("\n💾 Forcing save...")
    pm.force_save()
    print("💾 Force save completed")
    
    time.sleep(1.0)

    ## Test 5: Loading after all changes
    print("\n🔄 Testing loading after all changes...")
    pm_loaded2 = PersistentMap("test_positions.pkl", logger)
    print(f"📊 Loaded from file: {len(pm_loaded2)} positions")
    for key, value in pm_loaded2.items():
        print(f"   - {key}: {value}")
    
    ## Test 6: Data integrity verification
    print(f"\n🔍 Data integrity check:")
    print(f"   Original map: {len(pm)} records")
    print(f"   From file: {len(pm_loaded2)} records")
    print(f"   Data matches: {dict(pm) == dict(pm_loaded2)}")
    
    ## Cleanup: Stop all persistent map instances
    pm.stop()
    pm_loaded1.stop()
    pm_loaded2.stop()
    
    print("\n✅ Testing completed successfully!")


if __name__ == "__main__":
    main()
