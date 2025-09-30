#!/usr/bin/env bash
set -euo pipefail

python3 -m venv .venv
source .venv/bin/activate

pip install -U pip wheel
pip install -r requirements.txt

# Initialize DB if schema exists
[ -f data/schema.sql ] && shipy db init || true

# Start dev server (auto-reload)
export SHIPY_DEBUG=1
export SHIPY_BASE="$PWD"
shipy dev
