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

set -e

################################################################################
# @file setup.sh
# @brief Environment setup script for byninja-trading-bot.
#
# @details
# This script:
#   - Installs required system dependencies
#   - Creates Python virtual environment
#   - Upgrades pip
#   - Installs required Python packages
#
# @usage
#   ./setup.sh
#
################################################################################

FAILED=0

################################################################################
# @brief Error handler
################################################################################
on_error() {
  FAILED=1
  echo ""
  echo -e "\033[0;31m[ERROR] Setup failed. See logs above.\033[0m"
}
trap on_error ERR

################################################################################
# @section Dependencies
################################################################################
sudo apt update
sudo apt install python3-venv -y

################################################################################
# @section VirtualEnv Setup
################################################################################
python3 -m venv ./env
source ./env/bin/activate

################################################################################
# @section Package Installation
################################################################################
pip install --upgrade pip
pip install python-binance pandas numpy scipy

deactivate

################################################################################
# @section Output
################################################################################

BOLD='\033[1m'
CYAN='\033[0;36m'
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo ""

if [ "$FAILED" -eq 0 ]; then
  echo -e "/*"
  echo -e " * Project: ${BOLD}byninja-trading-bot${NC}"
  echo -e " * Status:  ${GREEN}Virtual environment configured successfully.${NC}"
else
  echo -e "/*"
  echo -e " * Project: ${BOLD}byninja-trading-bot${NC}"
  echo -e " * Status:  ${RED}FAILED to configure environment.${NC}"
fi

echo -e " * -----------------------------------------------------------------------------"
echo -e " * USAGE:"
echo -e " * Activate:   ${CYAN}source ./env/bin/activate${NC}"
echo -e " * Deactivate: ${CYAN}deactivate${NC}"
echo -e " * -----------------------------------------------------------------------------"
echo -e " */"
echo ""