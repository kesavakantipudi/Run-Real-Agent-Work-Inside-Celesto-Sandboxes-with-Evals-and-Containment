#!/bin/bash
set -e
if [ -f "$HOME/.config/celesto/env" ]; then
    set -a
    source "$HOME/.config/celesto/env"
    set +a
fi

export PROJECT_DIR="/mnt/c/Users/kesava_kantipudi/Desktop/GPP/Hackathon/Run Real Agent Work Inside Celesto Sandboxes with Evals and Containment"
cd "$PROJECT_DIR"
export PYTHONPATH="."
/home/kesava_kantipudi/.local/share/uv/tools/celesto/bin/python3 "$PROJECT_DIR/scripts/run_benchmarks.py"
