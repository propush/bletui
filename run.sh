#!/bin/sh
set -eu

SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
VENV="$SCRIPT_DIR/.venv"

if [ ! -d "$VENV" ]; then
  python3 -m venv "$VENV"
fi

. "$VENV/bin/activate"

pip install -r "$SCRIPT_DIR/requirements.txt"

exec python3 "$SCRIPT_DIR/app.py"
