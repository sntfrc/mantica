#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

nohup $SCRIPT_DIR/.venv/bin/python $SCRIPT_DIR/mantica.py &

