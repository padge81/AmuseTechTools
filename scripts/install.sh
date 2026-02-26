#!/usr/bin/env bash
set -euo pipefail

APP_NAME="amuse-tech-tools"
APP_DIR="${HOME}/AmuseTechTools"
VENV_DIR="${APP_DIR}/.venv"
SERVICE_DIR="${HOME}/.config/systemd/user"
SERVICE_FILE="${SERVICE_DIR}/${APP_NAME}.service"
START_SCRIPT="${APP_DIR}/system/kiosk/start_kiosk.sh"
SETUP_SCRIPT="${APP_DIR}/system/kiosk/setup_kiosk.sh"
URL="http://127.0.0.1:8080"
DESKTOP_DIR="${HOME}/Desktop"
DESKTOP_FILE="${DESKTOP_DIR}/AmuseTechTools.desktop"

ROTATE_DISPLAY="${ROTATE_DISPLAY:-right}"     # right|left|normal|inverted
DISPLAY_OUTPUT="${DISPLAY_OUTPUT:-DSI-1}"      # e.g. DSI-1
TOUCH_MATCH="${TOUCH_MATCH:-ft5x06|ft5406}"
HIDE_CURSOR="${HIDE_CURSOR:-1}"

log() { echo "[install] $*"; }

if ! command -v apt >/dev/null 2>&1; then
  echo "This installer currently supports Debian/Raspberry Pi OS (apt)." >&2
  exit 1
fi

log "Installing system dependencies..."
sudo apt update
sudo apt install -y \
  python3 python3-venv python3-pip \
  chromium-browser unclutter x11-xserver-utils xinput \
  wmctrl xdotool curl

log "Preparing Python virtual environment..."
python3 -m venv "${VENV_DIR}"
# shellcheck disable=SC1090
source "${VENV_DIR}/bin/activate"
pip install --upgrade pip

if [[ -s "${APP_DIR}/backend/requirements.txt" ]]; then
  pip install -r "${APP_DIR}/backend/requirements.txt"
else
  log "backend/requirements.txt is empty; installing minimum runtime packages."
  pip install flask
fi

deactivate || true

log "Writing kiosk start script: ${START_SCRIPT}"
mkdir -p "$(dirname "${START_SCRIPT}")"
cat > "${START_SCRIPT}" <<'START_EOF'
#!/usr/bin/env bash
set -euo pipefail

LOG="$HOME/amuse-tech-tools-kiosk.log"
exec >>"$LOG" 2>&1

echo "==== AmuseTechTools kiosk start: $(date) ===="

APP_DIR="$HOME/AmuseTechTools"
VENV_DIR="$APP_DIR/.venv"
URL="http://127.0.0.1:8080"

DISPLAY_OUTPUT="${DISPLAY_OUTPUT:-DSI-1}"
ROTATE_DISPLAY="${ROTATE_DISPLAY:-right}"
TOUCH_MATCH="${TOUCH_MATCH:-ft5x06|ft5406}"
HIDE_CURSOR="${HIDE_CURSOR:-1}"

export DISPLAY=:0
export XAUTHORITY="$HOME/.Xauthority"

for i in {1..40}; do
  if xset q >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

# Rotate panel output
xrandr --output "$DISPLAY_OUTPUT" --rotate "$ROTATE_DISPLAY" || echo "Display rotation skipped"

# Rotate touch matrix to match "right" rotation by default
TOUCH_NAME=$(xinput list --name-only | grep -Ei "$TOUCH_MATCH" | head -n1 || true)
if [[ -n "${TOUCH_NAME}" ]]; then
  if [[ "$ROTATE_DISPLAY" == "right" ]]; then
    xinput set-prop "$TOUCH_NAME" "Coordinate Transformation Matrix" 0 1 0 -1 0 1 0 0 1 || true
  elif [[ "$ROTATE_DISPLAY" == "left" ]]; then
    xinput set-prop "$TOUCH_NAME" "Coordinate Transformation Matrix" 0 -1 1 1 0 0 0 0 1 || true
  elif [[ "$ROTATE_DISPLAY" == "inverted" ]]; then
    xinput set-prop "$TOUCH_NAME" "Coordinate Transformation Matrix" -1 0 1 0 -1 1 0 0 1 || true
  else
    xinput set-prop "$TOUCH_NAME" "Coordinate Transformation Matrix" 1 0 0 0 1 0 0 0 1 || true
  fi
fi

if [[ "$HIDE_CURSOR" == "1" ]]; then
  pkill -f unclutter || true
  unclutter -idle 0 &
fi

cd "$APP_DIR"
if [[ -f "$VENV_DIR/bin/activate" ]]; then
  # shellcheck disable=SC1090
  source "$VENV_DIR/bin/activate"
fi

pkill -f "python3 app.py" || true
python3 app.py &

for i in {1..40}; do
  curl -s "$URL" >/dev/null && break
  sleep 1
done

pkill -f chromium || true
sleep 1

chromium-browser \
  --kiosk \
  --password-store=basic \
  --noerrdialogs \
  --disable-infobars \
  --disable-session-crashed-bubble \
  --disable-translate \
  --disable-features=TranslateUI \
  --check-for-update-interval=31536000 \
  "$URL" &

wait
START_EOF
chmod +x "${START_SCRIPT}"

log "Writing convenience setup wrapper: ${SETUP_SCRIPT}"
cat > "${SETUP_SCRIPT}" <<'SETUP_EOF'
#!/usr/bin/env bash
set -euo pipefail
"$HOME/AmuseTechTools/scripts/install.sh"
SETUP_EOF
chmod +x "${SETUP_SCRIPT}"

log "Installing user systemd service: ${SERVICE_FILE}"
mkdir -p "${SERVICE_DIR}"
cat > "${SERVICE_FILE}" <<SERVICE_EOF
[Unit]
Description=AmuseTechTools Kiosk
After=graphical-session.target
Wants=graphical-session.target

[Service]
Type=simple
ExecStart=${START_SCRIPT}
Restart=on-failure
Environment=DISPLAY=:0
Environment=XAUTHORITY=%h/.Xauthority
Environment=DISPLAY_OUTPUT=${DISPLAY_OUTPUT}
Environment=ROTATE_DISPLAY=${ROTATE_DISPLAY}
Environment=TOUCH_MATCH=${TOUCH_MATCH}
Environment=HIDE_CURSOR=${HIDE_CURSOR}

[Install]
WantedBy=default.target
SERVICE_EOF

systemctl --user daemon-reload
systemctl --user enable "${APP_NAME}.service"

log "Creating desktop launcher: ${DESKTOP_FILE}"
mkdir -p "${DESKTOP_DIR}"
cat > "${DESKTOP_FILE}" <<DESKTOP_EOF
[Desktop Entry]
Name=AmuseTechTools
Comment=Launch AmuseTechTools Kiosk
Exec=systemctl --user start ${APP_NAME}.service
Icon=utilities-terminal
Terminal=false
Type=Application
Categories=Utility;
DESKTOP_EOF
chmod +x "${DESKTOP_FILE}"

log "Enabling user linger for boot autostart"
if command -v loginctl >/dev/null 2>&1; then
  sudo loginctl enable-linger "${USER}" || true
else
  log "loginctl not available; skipping linger setup"
fi

log "Install complete."
log "Start now:   systemctl --user start ${APP_NAME}.service"
log "Enable at boot: linger is enabled for user ${USER}"
log "Desktop icon: ${DESKTOP_FILE}"
log "View logs:   journalctl --user -u ${APP_NAME}.service -f"
log "Rotate conf: edit ${SERVICE_FILE} env vars (DISPLAY_OUTPUT/ROTATE_DISPLAY)"
