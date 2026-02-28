#!/usr/bin/env bash
set -euo pipefail

APP_NAME="amuse-tech-tools"

systemctl --user start "${APP_NAME}.service"
systemctl --user --no-pager --full status "${APP_NAME}.service" | sed -n '1,20p'
cat > ~/AmuseTechTools/system/kiosk/start_kiosk.sh <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

LOG="$HOME/amuse-tech-tools-kiosk.log"
exec >>"$LOG" 2>&1

echo "==== AmuseTechTools kiosk start: $(date) ===="

APP_DIR="$HOME/AmuseTechTools"
VENV_DIR="$APP_DIR/.venv"
URL="http://127.0.0.1:8080"

HIDE_CURSOR="${HIDE_CURSOR:-1}"
BROWSER_FULLSCREEN="${BROWSER_FULLSCREEN:-1}"

# Under labwc/Wayland, Chromium typically runs under Xwayland.
export DISPLAY=:0
export XAUTHORITY="$HOME/.Xauthority"

# Wait for Xwayland to be ready (for chromium/wmctrl tools)
for i in {1..120}; do
  if xset q >/dev/null 2>&1; then
    break
  fi
  sleep 0.5
done

if [[ "$HIDE_CURSOR" == "1" ]]; then
  pkill -f unclutter || true
  unclutter -idle 0 &
fi

cd "$APP_DIR"

# Activate venv if present
if [[ -f "$VENV_DIR/bin/activate" ]]; then
  # shellcheck disable=SC1090
  source "$VENV_DIR/bin/activate"
fi

# Stop any previous backend (user-owned)
pkill -u "$USER" -f "python3.*app\.py" || true

# Run backend in "service-safe" mode (no reloader)
export FLASK_DEBUG=0
export FLASK_ENV=production
python3 app.py &
BACKEND_PID=$!

# Wait for backend to bind
for i in {1..60}; do
  if curl -fsS "$URL" >/dev/null 2>&1; then
    echo "Backend is up at $URL (pid=$BACKEND_PID)"
    break
  fi
  if ! kill -0 "$BACKEND_PID" >/dev/null 2>&1; then
    echo "ERROR: Backend process exited early"
    wait "$BACKEND_PID" || true
    exit 1
  fi
  sleep 0.5
done

if ! curl -fsS "$URL" >/dev/null 2>&1; then
  echo "ERROR: Backend did not become ready at $URL"
  exit 1
fi

# Launch Chromium in kiosk mode
pkill -u "$USER" -x chromium || true
pkill -u "$USER" -x chromium-browser || true
sleep 0.5

CHROMIUM_CMD=""
if command -v chromium-browser >/dev/null 2>&1; then
  CHROMIUM_CMD="chromium-browser"
elif command -v chromium >/dev/null 2>&1; then
  CHROMIUM_CMD="chromium"
else
  echo "No chromium executable found (chromium-browser/chromium)" >&2
  exit 1
fi

"${CHROMIUM_CMD}" \
  --kiosk \
  --start-fullscreen \
  --window-position=0,0 \
  --password-store=basic \
  --noerrdialogs \
  --disable-infobars \
  --disable-session-crashed-bubble \
  --disable-translate \
  --disable-features=TranslateUI \
  --check-for-update-interval=31536000 \
  "$URL" &

CHROME_PID=$!

# Best-effort fullscreen
if [[ "$BROWSER_FULLSCREEN" == "1" ]]; then
  sleep 2
  wmctrl -r "Chromium" -b add,fullscreen 2>/dev/null || true
fi

# If chromium exits, stop backend too
wait "$CHROME_PID" || true
echo "Chromium exited; stopping backend..."
kill "$BACKEND_PID" >/dev/null 2>&1 || true
wait "$BACKEND_PID" >/dev/null 2>&1 || true

EOF

chmod +x ~/AmuseTechTools/system/kiosk/start_kiosk.sh