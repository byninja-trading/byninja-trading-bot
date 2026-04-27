#!/bin/bash

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

################################################################################
# @file run.sh
# @brief Bot execution orchestrator for byninja-trading-bot.
#
# @details
# This script:
#   - Validates input arguments
#   - Activates Python virtual environment
#   - Runs selected module (trading or telegram)
#   - Restarts process automatically on crash
#   - Uses explicit PYTHONPATH for stable imports
#
# @usage
#   ./run.sh trading
#   ./run.sh telegram
#
################################################################################

################################################################################
# @section Settings
################################################################################
VENV_PATH="./env/bin/activate"
MODULE="$1"
RESTART_DELAY=3

################################################################################
# @section Colors
################################################################################
BOLD='\033[1m'
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

################################################################################
# @section Validation
################################################################################
if [[ "$MODULE" != "trading" && "$MODULE" != "telegram" ]]; then
    echo -e "${RED}Error:${NC} Invalid argument. Use 'trading' or 'telegram'."
    exit 1
fi

if [ ! -f "$VENV_PATH" ]; then
    echo -e "${RED}Error:${NC} Virtual environment not found at $VENV_PATH"
    echo "Run setup_env.sh first."
    exit 1
fi

################################################################################
# @section Environment_Setup
################################################################################
source "$VENV_PATH"

################################################################################
# @section Banner
################################################################################
echo -e "/*"
echo -e " * Project: ${BOLD}byninja-trading-bot${NC}"
echo -e " * Module:  ${YELLOW}$MODULE${NC}"
echo -e " * Status:  ${GREEN}Running with auto-restart...${NC}"
echo -e " * -----------------------------------------------------------------------------"
echo -e " * Press [CTRL+C] to stop the process."
echo -e " */"
echo ""

################################################################################
# @section Command_Selection
################################################################################
if [ "$MODULE" == "trading" ]; then
    CMD="from src.trading.main import main; main()"
else
    CMD="from src.telegram.main import main; main()"
fi

################################################################################
# @section Execution_Loop
# Restart process on failure, exit on clean stop
################################################################################
while true; do
    PYTHONPATH="$(pwd)/src" python3 -c "$CMD"

    EXIT_CODE=$?

    if [ $EXIT_CODE -ne 0 ]; then
        echo -e "\n${RED}[CRASH]${NC} Module $MODULE exited with code $EXIT_CODE"
        echo -e "${YELLOW}Restarting in $RESTART_DELAY seconds...${NC}"
        sleep $RESTART_DELAY
    else
        echo -e "\n${GREEN}[STOP]${NC} Module $MODULE exited normally"
        break
    fi
done