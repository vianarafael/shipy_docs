#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/srv/apps/shipy}"
REPO_DIR="${REPO_DIR:-$APP_DIR/repo}"
VENV="${VENV:-$APP_DIR/venv}"
SERVICE="${SERVICE:-shipy.service}"

# Load env and ensure SHIPY_BASE -> repo
[ -f "$APP_DIR/.env" ] && set -a && . "$APP_DIR/.env" && set +a
export SHIPY_BASE="${SHIPY_BASE:-$REPO_DIR}"

python3 -m venv "$VENV"
"$VENV/bin/pip" install -U pip wheel
if [ -f "$REPO_DIR/requirements.txt" ]; then
  "$VENV/bin/pip" install -r "$REPO_DIR/requirements.txt"
else
  "$VENV/bin/pip" install shipy-web "uvicorn[standard]"
fi

# Initialize DB if schema present (idempotent)
if [ -f "$REPO_DIR/data/schema.sql" ]; then
  (cd "$REPO_DIR" && "$VENV/bin/shipy" db init)
fi

sudo systemctl restart "$SERVICE"
sudo systemctl --no-pager --lines=20 status "$SERVICE" || true
