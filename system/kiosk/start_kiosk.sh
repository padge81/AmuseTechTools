#!/usr/bin/env bash
set -euo pipefail

LOG="$HOME/amuse-tech-tools-kiosk.log"
exec >>"$LOG" 2>&1

echo "==== AmuseTechTools kiosk start: $(date) ===="

APP_DIR="$HOME/AmuseTechTools"
VENV_DIR="$APP_DIR/.venv"
URL="http://127.0.0.1:8080"

export DISPLAY=:0
export XAUTHORITY="$HOME/.Xauthority"

# Wait for Xwayland
for i in {1..120}; do
  if xset q >/dev/null 2>&1; then
    break
  fi
  sleep 0.5
done

# Hide cursor
pkill -f unclutter || true
unclutter -idle 0 &

cd "$APP_DIR"

# Activate venv if present
if [[ -f "$VENV_DIR/bin/activate" ]]; then
  source "$VENV_DIR/bin/activate"
fi

# Stop any previous backend
pkill -u "$USER" -f "python3.*app\.py" || true

# Run backend WITHOUT debug/reloader
export FLASK_DEBUG=0
export FLASK_ENV=production
python3 app.py &
BACKEND_PID=$!

# Wait for backend
for i in {1..60}; do
  if curl -fsS "$URL" >/dev/null 2>&1; then
    echo "Backend ready"
    break
  fi
  if ! kill -0 "$BACKEND_PID" >/dev/null 2>&1; then
    echo "Backend exited early"
    exit 1
  fi
  sleep 0.5
done

if ! curl -fsS "$URL" >/dev/null 2>&1; then
  echo "Backend failed to bind"
  exit 1
fi

# Launch Chromium
pkill -u "$USER" -x chromium || true
pkill -u "$USER" -x chromium-browser || true
sleep 0.5

CHROMIUM_CMD="$(command -v chromium-browser || command -v chromium)"

"$CHROMIUM_CMD" \
  --kiosk \
  --start-fullscreen \
  --password-store=basic \
  --noerrdialogs \
  --disable-infobars \
  --disable-session-crashed-bubble \
  --disable-translate \
  "$URL" &

wait