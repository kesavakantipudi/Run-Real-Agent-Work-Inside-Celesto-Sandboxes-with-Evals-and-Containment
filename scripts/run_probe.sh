#!/bin/bash
set -e
# Load configuration if available
if [ -f "$HOME/.config/celesto/env" ]; then
    set -a
    source "$HOME/.config/celesto/env"
    set +a
fi

export PROJECT_DIR="/mnt/c/Users/kesava_kantipudi/Desktop/GPP/Hackathon/Run Real Agent Work Inside Celesto Sandboxes with Evals and Containment"
cd "$PROJECT_DIR"
/home/kesava_kantipudi/.local/share/uv/tools/celesto/bin/python3 "$PROJECT_DIR/scripts/probe_real_celesto.py"
