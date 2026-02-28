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

# --- Correct rotation method for Raspberry Pi OS Trixie + labwc + official DSI ---
# lcd_rotate values: 0=normal, 1=90° clockwise, 2=180°, 3=270°
LCD_ROTATE="${LCD_ROTATE:-1}"
BOOT_CONFIG=""

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
  "${CHROMIUM_PKG}" unclutter \
  wmctrl xdotool curl

# -------------------------------------------------------------------
# Set DSI rotation at boot (Wayland-safe; works with labwc + Xwayland)
# -------------------------------------------------------------------
if [[ -f /boot/firmware/config.txt ]]; then
  BOOT_CONFIG="/boot/firmware/config.txt"
elif [[ -f /boot/config.txt ]]; then
  # Older systems; on Trixie you generally want /boot/firmware/config.txt
  BOOT_CONFIG="/boot/config.txt"
fi

if [[ -n "${BOOT_CONFIG}" ]]; then
  log "Setting official DSI rotation in ${BOOT_CONFIG} (lcd_rotate=${LCD_ROTATE})"
  # Replace if exists, otherwise append
  if sudo grep -qE '^\s*lcd_rotate=' "${BOOT_CONFIG}"; then
    sudo sed -i -E "s/^\s*lcd_rotate=.*/lcd_rotate=${LCD_ROTATE}/" "${BOOT_CONFIG}"
  else
    echo "lcd_rotate=${LCD_ROTATE}" | sudo tee -a "${BOOT_CONFIG}" >/dev/null
  fi
  log "Rotation set. Reboot required for rotation to take effect."
else
  log "Warning: could not locate boot config file to set lcd_rotate. Skipping rotation setup."
fi

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
BROWSER_LOCK_OUTPUT="${BROWSER_LOCK_OUTPUT:-1}"

# NOTE:
# On Raspberry Pi OS Trixie + labwc (Wayland), do NOT rotate using xrandr/xinput.
# Rotation is done via /boot/firmware/config.txt using lcd_rotate=...

export DISPLAY=:0
export XAUTHORITY="$HOME/.Xauthority"

# Wait for Xwayland DISPLAY to exist (needed only for Chromium + optional wmctrl/xdotool)
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

# Best-effort fullscreen (may be limited under Wayland; works via Xwayland in many cases)
if [[ "$BROWSER_LOCK_OUTPUT" == "