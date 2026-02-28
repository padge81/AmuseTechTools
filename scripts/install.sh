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

# Kiosk behavior knobs (kept)
HIDE_CURSOR="${HIDE_CURSOR:-1}"
BROWSER_FULLSCREEN="${BROWSER_FULLSCREEN:-1}"

# --- Correct rotation method for Trixie + labwc (Wayland) + official DSI ---
# Use KMS/kernel rotation (NOT xrandr). Degrees: 0|90|180|270
DSI_ROTATE_DEG="${DSI_ROTATE_DEG:-90}"

log() { echo "[install] $*"; }

run_as_target_user() {
  local uid
  uid="$(id -u "${TARGET_USER}")"
  sudo -u "${TARGET_USER}" env XDG_RUNTIME_DIR="/run/user/${uid}" "$@"
}

require_apt() {
  if ! command -v apt >/dev/null 2>&1; then
    echo "This installer currently supports Debian/Raspberry Pi OS (apt)." >&2
    exit 1
  fi
}

backup_file() {
  local f="$1"
  if [[ -f "$f" ]]; then
    sudo cp -a "$f" "${f}.bak.$(date +%Y%m%d-%H%M%S)"
  fi
}

set_dsi_rotation_kms() {
  local cmdline="/boot/firmware/cmdline.txt"
  local config="/boot/firmware/config.txt"

  if [[ ! -f "$cmdline" ]]; then
    echo "[install] ERROR: ${cmdline} not found" >&2
    exit 1
  fi
  if [[ ! -f "$config" ]]; then
    echo "[install] ERROR: ${config} not found" >&2
    exit 1
  fi

  case "${DSI_ROTATE_DEG}" in
    0|90|180|270) ;;
    *)
      echo "[install] ERROR: DSI_ROTATE_DEG must be 0, 90, 180, or 270 (got '${DSI_ROTATE_DEG}')" >&2
      exit 1
      ;;
  esac

  log "Configuring official DSI rotation for Wayland/KMS (DSI_ROTATE_DEG=${DSI_ROTATE_DEG})"

  # --- cmdline: single line; append/replace video=DSI-1:... token
  backup_file "$cmdline"
  local current
  current="$(sudo cat "$cmdline")"

  # Remove any existing video=DSI-1:... token
  current="$(echo "$current" \
    | sed -E 's/(^| )video=DSI-1:[^ ]+//g' \
    | sed -E 's/  +/ /g' \
    | sed -E 's/^ //; s/ $//')"

  # Add ours
  local new
  new="${current} video=DSI-1:800x480@60,rotate=${DSI_ROTATE_DEG}"
  echo "$new" | sudo tee "$cmdline" >/dev/null

  # --- config.txt: ensure overlays for DSI touchscreen under KMS and fix touch axis
  backup_file "$config"

  # Touch params mapping (practical defaults):
  #  - 0: none
  #  - 180: invx,invy
  #  - 90/270: swapxy plus one inversion (can vary by mounting; see notes below)
  local touch_params=""
  case "${DSI_ROTATE_DEG}" in
    0)   touch_params="" ;;
    180) touch_params=",invx,invy" ;;
    90)  touch_params=",swapxy,invy" ;;   # if touch ends up mirrored, change to ",swapxy,invx"
    270) touch_params=",swapxy,invx" ;;   # if touch ends up mirrored, change to ",swapxy,invy"
  esac

  # Remove existing vc4-kms-dsi-7inch overlay lines to avoid duplicates
  sudo sed -i -E '/^\s*dtoverlay=vc4-kms-dsi-7inch([, ].*)?$/d' "$config"

  # Ensure vc4-kms-v3d exists (commonly needed on Pi OS KMS stacks)
  if ! sudo grep -qE '^\s*dtoverlay=vc4-kms-v3d\b' "$config"; then
    echo "dtoverlay=vc4-kms-v3d" | sudo tee -a "$config" >/dev/null
  fi

  echo "dtoverlay=vc4-kms-dsi-7inch${touch_params}" | sudo tee -a "$config" >/dev/null

  log "Rotation set via:"
  log "  ${cmdline}: video=DSI-1:800x480@60,rotate=${DSI_ROTATE_DEG}"
  log "  ${config}:  dtoverlay=vc4-kms-dsi-7inch${touch_params}"
  log "Reboot REQUIRED for rotation to take effect."
}

# --- main ---
require_apt

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
  "${CHROMIUM_PKG}" \
  unclutter wmctrl xdotool curl

# Correct rotation method for your setup (Trixie + labwc + DSI official touchscreen)
set_dsi_rotation_kms

log "Preparing Python virtual environment..."
if [[ ! -d "${VENV_DIR}" ]]; then
  sudo -u "${TARGET_USER}" python3 -m venv "${VENV_DIR}"
fi
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

HIDE_CURSOR="${HIDE_CURSOR:-1}"
BROWSER_FULLSCREEN="${BROWSER_FULLSCREEN:-1}"

# IMPORTANT (Trixie + labwc/Wayland):
# Display + touch rotation is handled at boot via:
#  - /boot/firmware/cmdline.txt: video=DSI-1:800x480@60,rotate=...
#  - /boot/firmware/config.txt:  dtoverlay=vc4-kms-dsi-7inch,...
# Do NOT use xrandr/xinput rotation here.

export DISPLAY=:0
export XAUTHORITY="$HOME/.Xauthority"

# Wait for Xwayland (Chromium + wmctrl/xdotool rely on this)
for i in {1..80}; do
  if xset q >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

if [[ "$HIDE_CURSOR" == "1" ]]; then
  pkill -f unclutter || true
  unclutter -idle 0 &
fi

cd "$APP_DIR"

if [[ -f "$VENV_DIR/bin/activate" ]]; then
  # shellcheck disable=SC1090
  source "$VENV_DIR/bin/activate"
fi

# Start backend
pkill -f "python3 app.py" || true
python3 app.py &

# Wait for backend
for i in {1..40}; do
  curl -s "$URL" >/dev/null && break
  sleep 1
done

# Start Chromium kiosk
pkill -u "$USER" -x chromium || true
pkill -u "$USER" -x chromium-browser || true
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

# Best-effort fullscreen (Wayland limits WM control; Xwayland often still allows this)
if [[ "$BROWSER_FULLSCREEN" == "1" ]]; then
  sleep 2
  # Try by title first, then by class
  wmctrl -r "Chromium" -b add,fullscreen 2>/dev/null || true
  WIN_ID="$(xdotool search --onlyvisible --class chromium 2>/dev/null | head -n1 || true)"
  if [[ -n "${WIN_ID}" ]]; then
    wmctrl -i -r "${WIN_ID}" -b add,fullscreen 2>/dev/null || true
  fi
fi

wait
START_EOF

chmod +x "${START_SCRIPT}"
chown "${TARGET_USER}:${TARGET_USER}" "${START_SCRIPT}"

log "Writing convenience setup wrapper: ${SETUP_SCRIPT}"
mkdir -p "$(dirname "${SETUP_SCRIPT}")"
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
Environment=HIDE_CURSOR=${HIDE_CURSOR}
Environment=BROWSER_FULLSCREEN=${BROWSER_FULLSCREEN}

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
Environment=HIDE_CURSOR=${HIDE_CURSOR}
Environment=BROWSER_FULLSCREEN=${BROWSER_FULLSCREEN}

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
log "REBOOT REQUIRED for DSI rotation to apply."
log "Start now:   systemctl --user start ${APP_NAME}.service"
log "System boot autostart enabled: sudo systemctl status ${APP_NAME}.service"
log "Desktop icon: ${DESKTOP_FILE}"
log "View logs:   journalctl --user -u ${APP_NAME}.service -f"
log "Rotation set: /boot/firmware/cmdline.txt + /boot/firmware/config.txt (DSI_ROTATE_DEG=${DSI_ROTATE_DEG})"