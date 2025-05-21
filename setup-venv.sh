#!/bin/bash
set -e

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

# Activate the environment
source .venv/bin/activate

# Upgrade pip and install required packages
pip install --upgrade pip
pip install flask replicate requests
