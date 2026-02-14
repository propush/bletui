#!/bin/bash
# Launcher script for BLE TUI app
# Opens Terminal and runs the run.sh script

# Get absolute path to the run.sh script
# So run.sh is at ../../../run.sh relative to this script
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
RUN_SCRIPT=$SCRIPT_DIR/../../../run.sh

# Verify run.sh exists
if [ ! -f "$RUN_SCRIPT" ]; then
    osascript -e 'display dialog "Error: Could not find run.sh at '"$RUN_SCRIPT"'" buttons {"OK"} default button 1 with icon stop'
    exit 1
fi

# Open Terminal and execute run.sh
open -a Terminal "$RUN_SCRIPT"
