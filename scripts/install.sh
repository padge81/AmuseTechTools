#!/usr/bin/env bash
set -euo pipefail

APP_NAME="amuse-tech-tools"
TARGET_USER="${SUDO_USER:-${USER}}"
TARGET_HOME="$(getent passwd "${TARGET_USER}" | cut -d: -f6)"
if [[ -z "${TARGET_HOME}" ]]; then
  echo "Could not resolve home directory for user '${TARGET_USER}'" >&2
  exit 1
fi

APP_DIR="${TARGET_HOME}/AmuseTechTools"
VENV_DIR="${APP_DIR}/.venv"
SERVICE_DIR="${TARGET_HOME}/.config/systemd/user"
SERVICE_FILE="${SERVICE_DIR}/${APP_NAME}.service"
SERVICE_WANTS_DIR="${SERVICE_DIR}/default.target.wants"
SYSTEM_SERVICE_FILE="/etc/systemd/system/${APP_NAME}.service"
AUTOSTART_DIR="${TARGET_HOME}/.config/autostart"
AUTOSTART_FILE="${AUTOSTART_DIR}/${APP_NAME}.desktop"
START_SCRIPT="${APP_DIR}/system/kiosk/start_kiosk.sh"
SETUP_SCRIPT="${APP_DIR}/system/kiosk/setup_kiosk.sh"
URL="http://127.0.0.1:8080"
DESKTOP_DIR="${TARGET_HOME}/Desktop"
DESKTOP_FILE="${DESKTOP_DIR}/AmuseTechTools.desktop"

ROTATE_DISPLAY="${ROTATE_DISPLAY:-right}"     # right|left|normal|inverted
DISPLAY_OUTPUT="${DISPLAY_OUTPUT:-DSI-1}"      # e.g. DSI-1
TOUCH_MATCH="${TOUCH_MATCH:-ft5x06|ft5406}"
HIDE_CURSOR="${HIDE_CURSOR:-1}"
BROWSER_LOCK_OUTPUT="${BROWSER_LOCK_OUTPUT:-1}"

log() { echo "[install] $*"; }

run_as_target_user() {
  local uid
  uid="$(id -u "${TARGET_USER}")"
  sudo -u "${TARGET_USER}" env XDG_RUNTIME_DIR="/run/user/${uid}" "$@"
}

if ! command -v apt >/dev/null 2>&1; then
  echo "This installer currently supports Debian/Raspberry Pi OS (apt)." >&2
  exit 1
fi

log "Installing system dependencies..."
sudo apt update

CHROMIUM_PKG=""
if apt-cache show chromium >/dev/null 2>&1; then
  CHROMIUM_PKG="chromium"
elif apt-cache show chromium-browser >/dev/null 2>&1; then
  CHROMIUM_PKG="chromium-browser"
else
  echo "Could not find chromium-browser or chromium package in apt sources." >&2
  exit 1
fi

log "Using Chromium package: ${CHROMIUM_PKG}"
sudo apt install -y \
  python3 python3-venv python3-pip \
  "${CHROMIUM_PKG}" unclutter x11-xserver-utils xinput \
  wmctrl xdotool curl

log "Preparing Python virtual environment..."
sudo -u "${TARGET_USER}" python3 -m venv "${VENV_DIR}"
run_as_target_user "${VENV_DIR}/bin/pip" install --upgrade pip

if [[ -s "${APP_DIR}/backend/requirements.txt" ]]; then
  run_as_target_user "${VENV_DIR}/bin/pip" install -r "${APP_DIR}/backend/requirements.txt"
else
  log "backend/requirements.txt is empty; installing minimum runtime packages."
  run_as_target_user "${VENV_DIR}/bin/pip" install flask
fi

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
BROWSER_LOCK_OUTPUT="${BROWSER_LOCK_OUTPUT:-1}"

export DISPLAY=:0
export XAUTHORITY="$HOME/.Xauthority"

for i in {1..80}; do
  if xset q >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

resolve_output_name() {
  local want="$1"
  local candidate
  while read -r candidate; do
    [[ "$candidate" == "$want" ]] && { echo "$candidate"; return 0; }
    [[ "${candidate^^}" == "${want^^}" ]] && { echo "$candidate"; return 0; }
  done < <(xrandr --query | awk '/ connected/{print $1}')
  return 1
}

wait_for_output_connected() {
  local out="$1"
  local i
  for i in {1..60}; do
    if xrandr --query | awk '/ connected/{print $1}' | grep -Fxq "$out"; then
      return 0
    fi
    sleep 1
  done
  return 1
}

get_output_geometry() {
  local out="$1"
  xrandr --current | awk -v out="$out" '$1==out && $2=="connected" {for(i=1;i<=NF;i++) if($i ~ /[0-9]+x[0-9]+\+[0-9]+\+[0-9]+/) {print $i; exit}}'
}

OUTPUT_NAME="$DISPLAY_OUTPUT"
if ! OUTPUT_NAME="$(resolve_output_name "$DISPLAY_OUTPUT")"; then
  OUTPUT_NAME="$DISPLAY_OUTPUT"
fi

# Rotate selected panel output and make it primary so kiosk opens there.
if wait_for_output_connected "$OUTPUT_NAME"; then
  xrandr --output "$OUTPUT_NAME" --auto --rotate "$ROTATE_DISPLAY" --primary || echo "Display rotation/primary set skipped"
else
  echo "Output '$OUTPUT_NAME' not detected as connected in time"
fi

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

# Best-effort lock to selected output in X11 WM if requested.
if [[ "$BROWSER_LOCK_OUTPUT" == "1" ]]; then
  GEOM="$(get_output_geometry "$OUTPUT_NAME" || true)"
  sleep 3
  if [[ -n "$GEOM" ]]; then
    SIZE="${GEOM%%+*}"
    REST="${GEOM#*+}"
    XPOS="${REST%%+*}"
    YPOS="${REST#*+}"
    WIDTH="${SIZE%x*}"
    HEIGHT="${SIZE#*x}"
    wmctrl -r "Chromium" -e "0,${XPOS},${YPOS},${WIDTH},${HEIGHT}" || true
  fi
  wmctrl -r "Chromium" -b add,fullscreen || true
fi

wait
START_EOF
chmod +x "${START_SCRIPT}"
chown "${TARGET_USER}:${TARGET_USER}" "${START_SCRIPT}"

log "Writing convenience setup wrapper: ${SETUP_SCRIPT}"
cat > "${SETUP_SCRIPT}" <<'SETUP_EOF'
#!/usr/bin/env bash
set -euo pipefail
"$HOME/AmuseTechTools/scripts/install.sh"
SETUP_EOF
chmod +x "${SETUP_SCRIPT}"
chown "${TARGET_USER}:${TARGET_USER}" "${SETUP_SCRIPT}"

log "Installing user systemd service: ${SERVICE_FILE}"
mkdir -p "${SERVICE_DIR}"
cat > "${SERVICE_FILE}" <<SERVICE_EOF
[Unit]
Description=AmuseTechTools Kiosk
After=graphical-session.target graphical.target
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
Environment=BROWSER_LOCK_OUTPUT=${BROWSER_LOCK_OUTPUT}

[Install]
WantedBy=default.target
SERVICE_EOF
chown -R "${TARGET_USER}:${TARGET_USER}" "${SERVICE_DIR}"

# Ensure autostart even when systemctl --user cannot enable in non-interactive sudo contexts.
mkdir -p "${SERVICE_WANTS_DIR}"
ln -sfn "../${APP_NAME}.service" "${SERVICE_WANTS_DIR}/${APP_NAME}.service"
chown -R "${TARGET_USER}:${TARGET_USER}" "${SERVICE_DIR}"

if run_as_target_user systemctl --user daemon-reload && run_as_target_user systemctl --user enable "${APP_NAME}.service"; then
  log "User service enabled for ${TARGET_USER}."
else
  log "Warning: could not access user systemd bus for ${TARGET_USER} during install."
  log "When logged in as ${TARGET_USER}, run:"
  log "  systemctl --user daemon-reload"
  log "  systemctl --user enable ${APP_NAME}.service"
fi

log "Installing system service for boot autostart: ${SYSTEM_SERVICE_FILE}"
cat > "${SYSTEM_SERVICE_FILE}" <<SYSTEM_SERVICE_EOF
[Unit]
Description=AmuseTechTools Kiosk (system boot)
After=network-online.target display-manager.service graphical.target
Wants=network-online.target display-manager.service graphical.target

[Service]
Type=simple
User=${TARGET_USER}
Group=${TARGET_USER}
WorkingDirectory=${APP_DIR}
ExecStart=${START_SCRIPT}
Restart=on-failure
Environment=DISPLAY=:0
Environment=XAUTHORITY=${TARGET_HOME}/.Xauthority
Environment=DISPLAY_OUTPUT=${DISPLAY_OUTPUT}
Environment=ROTATE_DISPLAY=${ROTATE_DISPLAY}
Environment=TOUCH_MATCH=${TOUCH_MATCH}
Environment=HIDE_CURSOR=${HIDE_CURSOR}
Environment=BROWSER_LOCK_OUTPUT=${BROWSER_LOCK_OUTPUT}

[Install]
WantedBy=multi-user.target
SYSTEM_SERVICE_EOF

sudo systemctl daemon-reload
sudo systemctl enable "${APP_NAME}.service"

log "Creating desktop autostart entry: ${AUTOSTART_FILE}"
mkdir -p "${AUTOSTART_DIR}"
cat > "${AUTOSTART_FILE}" <<AUTOSTART_EOF
[Desktop Entry]
Type=Application
Name=AmuseTechTools Autostart
Exec=systemctl --user start ${APP_NAME}.service
X-GNOME-Autostart-enabled=true
AUTOSTART_EOF
chown "${TARGET_USER}:${TARGET_USER}" "${AUTOSTART_FILE}"

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
chown "${TARGET_USER}:${TARGET_USER}" "${DESKTOP_FILE}"

log "Enabling user linger for boot autostart"
if command -v loginctl >/dev/null 2>&1; then
  sudo loginctl enable-linger "${TARGET_USER}" || true
else
  log "loginctl not available; skipping linger setup"
fi

log "Install complete."
log "Start now:   systemctl --user start ${APP_NAME}.service"
log "System boot autostart enabled: sudo systemctl status ${APP_NAME}.service"
log "Enable at boot: linger is enabled for user ${TARGET_USER}"
log "Desktop icon: ${DESKTOP_FILE}"
log "View logs:   journalctl --user -u ${APP_NAME}.service -f"
log "Rotate conf: edit ${SERVICE_FILE} env vars (DISPLAY_OUTPUT/ROTATE_DISPLAY)"
