#!/usr/bin/env bash
set -euo pipefail

# =========================
# AmuseTechTools Installer
# Raspberry Pi OS / Debian 13 (Trixie) + LightDM + labwc (Wayland)
#
# Rotation handled via labwc + wlr-randr
# I2C/EDID support via python3-smbus + smbus2
# =========================

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

START_SCRIPT="${APP_DIR}/system/kiosk/start_kiosk.sh"
SETUP_SCRIPT="${APP_DIR}/system/kiosk/setup_kiosk.sh"

URL="http://127.0.0.1:8080"

DESKTOP_DIR="${TARGET_HOME}/Desktop"
DESKTOP_FILE="${DESKTOP_DIR}/AmuseTechTools.desktop"

HIDE_CURSOR="${HIDE_CURSOR:-1}"
BROWSER_FULLSCREEN="${BROWSER_FULLSCREEN:-1}"

ROTATE_DEG="${ROTATE_DEG:-270}"
WAYLAND_OUTPUT="${WAYLAND_OUTPUT:-DSI-1}"

BOOT_CONFIG="/boot/firmware/config.txt"
CMDLINE="/boot/firmware/cmdline.txt"

log() { echo "[install] $*"; }

run_as_target_user() {
  local uid
  uid="$(id -u "${TARGET_USER}")"
  sudo -u "${TARGET_USER}" env XDG_RUNTIME_DIR="/run/user/${uid}" "$@"
}

require_apt() {
  command -v apt >/dev/null 2>&1 || {
    echo "Debian/Raspberry Pi OS required." >&2
    exit 1
  }
}

validate_rotation() {
  case "$ROTATE_DEG" in
    0|90|180|270) ;;
    *) echo "ROTATE_DEG must be 0,90,180,270" >&2; exit 1 ;;
  esac
}

install_labwc_rotation_autostart() {
  local labwc_dir="${TARGET_HOME}/.config/labwc"
  local labwc_autostart="${labwc_dir}/autostart"

  log "Installing labwc rotation: ${WAYLAND_OUTPUT} -> ${ROTATE_DEG}"

  mkdir -p "$labwc_dir"

cat > "$labwc_autostart" <<EOF
#!/usr/bin/env bash
set -e

export XDG_RUNTIME_DIR="\${XDG_RUNTIME_DIR:-/run/user/\$(id -u)}"
export WAYLAND_DISPLAY="\${WAYLAND_DISPLAY:-\$(ls "\$XDG_RUNTIME_DIR" 2>/dev/null | grep '^wayland-' | head -n1)}"

# Try a few times because outputs appear slightly after compositor start.
for i in \$(seq 1 30); do
  # Rotate the DSI output
  wlr-randr --output "${WAYLAND_OUTPUT}" --pos 0,0 --transform ${ROTATE_DEG} >/dev/null 2>&1 || true

  # Disable HDMI so kiosk cannot appear there
  # Common name on Pi: HDMI-A-1 (change if yours differs)
  wlr-randr --output "HDMI-A-1" --off >/dev/null 2>&1 || true

  # If DSI command succeeded, we're good enough
  wlr-randr --output "${WAYLAND_OUTPUT}" >/dev/null 2>&1 && exit 0
  sleep 0.3
done

exit 0
EOF

  chmod +x "$labwc_autostart"
  chown -R "${TARGET_USER}:${TARGET_USER}" "$labwc_dir"
}

# --------------------------
# MAIN
# --------------------------

require_apt
validate_rotation

log "Installing system dependencies..."

sudo apt update

CHROMIUM_PKG=""
if apt-cache show chromium >/dev/null 2>&1; then
  CHROMIUM_PKG="chromium"
elif apt-cache show chromium-browser >/dev/null 2>&1; then
  CHROMIUM_PKG="chromium-browser"
else
  echo "Chromium not found in apt sources." >&2
  exit 1
fi

sudo apt install -y \
  python3 python3-venv python3-pip \
  python3-smbus i2c-tools \
  "${CHROMIUM_PKG}" \
  dbus-user-session \
  onboard \
  x11-utils \
  unclutter wmctrl xdotool curl wlr-randr

install_labwc_rotation_autostart

log "Preparing Python virtual environment..."

# Always recreate venv cleanly to avoid contamination
if [[ -d "${VENV_DIR}" ]]; then
  log "Removing existing virtual environment..."
  rm -rf "${VENV_DIR}"
fi

log "Creating virtual environment (with system site packages)..."
sudo -u "${TARGET_USER}" python3 -m venv --system-site-packages "${VENV_DIR}"

run_as_target_user "${VENV_DIR}/bin/pip" install --upgrade pip

if [[ -s "${APP_DIR}/backend/requirements.txt" ]]; then
  run_as_target_user "${VENV_DIR}/bin/pip" install -r "${APP_DIR}/backend/requirements.txt"
else
  run_as_target_user "${VENV_DIR}/bin/pip" install flask
fi

# Ensure smbus support exists in venv
run_as_target_user "${VENV_DIR}/bin/pip" install smbus2

log "Writing kiosk start script..."

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

export DISPLAY=:0
export XAUTHORITY="$HOME/.Xauthority"

for i in {1..120}; do
  xset q >/dev/null 2>&1 && break
  sleep 0.5
done

pkill -f unclutter || true
unclutter -idle 0 &

cd "$APP_DIR"

if [[ -f "$VENV_DIR/bin/activate" ]]; then
  source "$VENV_DIR/bin/activate"
fi

pkill -u "$USER" -f "python3 app.py" || true
python3 app.py &
BACKEND_PID=$!

for i in {1..60}; do
  curl -fsS "$URL" >/dev/null 2>&1 && break
  sleep 0.5
done

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
# Start on-screen keyboard (X11): onboard
export XDG_RUNTIME_DIR="/run/user/$(id -u)"
export DBUS_SESSION_BUS_ADDRESS="unix:path=$XDG_RUNTIME_DIR/bus"

pkill -x onboard 2>/dev/null || true
onboard >/dev/null 2>&1 &
sleep 1
wmctrl -xa "onboard.Onboard" -b add,hidden 2>/dev/null || true

wait
START_EOF

chmod +x "${START_SCRIPT}"
chown "${TARGET_USER}:${TARGET_USER}" "${START_SCRIPT}"

log "Installing systemd user service..."

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

[Install]
WantedBy=default.target
SERVICE_EOF

chown -R "${TARGET_USER}:${TARGET_USER}" "${SERVICE_DIR}"

run_as_target_user systemctl --user daemon-reload
run_as_target_user systemctl --user enable "${APP_NAME}.service"

sudo loginctl enable-linger "${TARGET_USER}" || true

log "Creating desktop launcher..."

mkdir -p "${DESKTOP_DIR}"

cat > "${DESKTOP_FILE}" <<DESKTOP_EOF
[Desktop Entry]
Name=AmuseTechTools
Exec=systemctl --user start ${APP_NAME}.service
Terminal=false
Type=Application
Categories=Utility;
DESKTOP_EOF

chmod +x "${DESKTOP_FILE}"
chown "${TARGET_USER}:${TARGET_USER}" "${DESKTOP_FILE}"

log "Install complete."
log "Reboot recommended."