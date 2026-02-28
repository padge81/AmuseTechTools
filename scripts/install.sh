#!/usr/bin/env bash
set -euo pipefail

# =========================
# AmuseTechTools Installer
# Raspberry Pi OS / Debian 13 (Trixie) + LightDM + labwc (Wayland)
#
# Rotation: handled by labwc (Wayland) using wlr-randr (NOT xrandr).
# Touch: do NOT apply xinput matrices. If you previously added swapxy/invx/invy
#        in config.txt, this installer will remove those params to avoid
#        double-transform once Wayland rotation is enabled.
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

# Kiosk knobs
HIDE_CURSOR="${HIDE_CURSOR:-1}"
BROWSER_FULLSCREEN="${BROWSER_FULLSCREEN:-1}"

# Rotation: Wayland (labwc) output transform in degrees
# Supported by wlr-randr: 0, 90, 180, 270
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

backup_file() {
  local f="$1"
  if [[ -f "$f" ]]; then
    sudo cp -a "$f" "${f}.bak.$(date +%Y%m%d-%H%M%S)"
  fi
}

require_apt() {
  if ! command -v apt >/dev/null 2>&1; then
    echo "This installer currently supports Debian/Raspberry Pi OS (apt)." >&2
    exit 1
  fi
}

validate_rotation() {
  case "$ROTATE_DEG" in
    0|90|180|270) ;;
    *)
      echo "[install] ERROR: ROTATE_DEG must be 0, 90, 180, or 270 (got '$ROTATE_DEG')" >&2
      exit 1
      ;;
  esac
}

cleanup_old_kernel_rotation() {
  # Optional cleanup:
  # If you previously added lcd_rotate= or cmdline video=DSI-1:...rotate=...
  # those can conflict or be confusing. We remove them to rely on Wayland rotation.
  if [[ -f "$BOOT_CONFIG" ]]; then
    backup_file "$BOOT_CONFIG"
    # remove lcd_rotate lines
    sudo sed -i -E '/^\s*lcd_rotate\s*=/d' "$BOOT_CONFIG" || true
    # remove vc4-kms-dsi-7inch lines that include touch params swapxy/invx/invy
    # then ensure the base overlay exists without params (safe)
    if sudo grep -qE '^\s*dtoverlay=vc4-kms-dsi-7inch' "$BOOT_CONFIG"; then
      sudo sed -i -E '/^\s*dtoverlay=vc4-kms-dsi-7inch.*(swapxy|invx|invy).*/d' "$BOOT_CONFIG" || true
      if ! sudo grep -qE '^\s*dtoverlay=vc4-kms-dsi-7inch(\s|$)' "$BOOT_CONFIG"; then
        echo "dtoverlay=vc4-kms-dsi-7inch" | sudo tee -a "$BOOT_CONFIG" >/dev/null
      fi
    fi
  fi

  if [[ -f "$CMDLINE" ]]; then
    backup_file "$CMDLINE"
    local current
    current="$(sudo cat "$CMDLINE")"
    # remove any existing video=DSI-1:... token
    current="$(echo "$current" \
      | sed -E 's/(^| )video=DSI-1:[^ ]+//g' \
      | sed -E 's/  +/ /g' \
      | sed -E 's/^ //; s/ $//')"
    echo "$current" | sudo tee "$CMDLINE" >/dev/null
  fi
}

install_labwc_rotation_autostart() {
  # labwc reads ~/.config/labwc/autostart and runs it on session start.
  # We set rotation there using wlr-randr.
  local labwc_dir="${TARGET_HOME}/.config/labwc"
  local labwc_autostart="${labwc_dir}/autostart"

  log "Installing labwc autostart rotation (Wayland) for output ${WAYLAND_OUTPUT} -> ${ROTATE_DEG}°"
  mkdir -p "$labwc_dir"

  cat > "$labwc_autostart" <<EOF
#!/usr/bin/env bash
set -e

# labwc autostart (runs inside the Wayland session)
# Rotate output using wlr-randr.
# If the output name differs, run: wlr-randr (in a terminal on the Pi) and update it.

# Ensure we have a runtime dir (normally already set inside session)
export XDG_RUNTIME_DIR="\${XDG_RUNTIME_DIR:-/run/user/\$(id -u)}"
export WAYLAND_DISPLAY="\${WAYLAND_DISPLAY:-\$(ls "\$XDG_RUNTIME_DIR" 2>/dev/null | grep -E '^wayland-' | head -n1)}"

# Try a few times because outputs may appear slightly after compositor start.
for i in \$(seq 1 30); do
  wlr-randr --output "${WAYLAND_OUTPUT}" --transform ${ROTATE_DEG} >/dev/null 2>&1 && exit 0
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
  echo "Could not find chromium-browser or chromium package in apt sources." >&2
  exit 1
fi

log "Using Chromium package: ${CHROMIUM_PKG}"
sudo apt install -y \
  python3 python3-venv python3-pip \
  "${CHROMIUM_PKG}" \
  unclutter wmctrl xdotool curl \
  wlr-randr

# If you previously tried kernel/config rotation + touch params, clean them up now.
# This keeps things consistent: Wayland handles the display rotation.
log "Cleaning up old kernel/cmdline rotation and touch param hacks (if present)..."
cleanup_old_kernel_rotation

# Install Wayland/labwc rotation
install_labwc_rotation_autostart

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
# Display rotation is handled by labwc using wlr-randr via:
#   ~/.config/labwc/autostart
# Do NOT use xrandr/xinput rotation here.

# Chromium runs under Xwayland in many labwc setups.
# These env vars help tools that still speak X11 (xset/wmctrl/xdotool).
export DISPLAY=:0
export XAUTHORITY="$HOME/.Xauthority"

# Wait for Xwayland DISPLAY to exist (Chromium + wmctrl/xdotool rely on this)
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

if [[ -f "$VENV_DIR/bin/activate" ]]; then
  # shellcheck disable=SC1090
  source "$VENV_DIR/bin/activate"
fi

# Start backend
pkill -f "python3 app.py" || true
python3 app.py &

# Wait for backend
for i in {1..60}; do
  curl -s "$URL" >/dev/null && break
  sleep 0.5
done

# Start Chromium kiosk
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

# Best-effort fullscreen (Wayland limits WM control; Xwayland often still allows this)
if [[ "$BROWSER_FULLSCREEN" == "1" ]]; then
  sleep 2
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

log "Installing systemd USER service: ${SERVICE_FILE}"
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

log "Install complete."
log "Rotation is handled by labwc autostart:"
log "  ${TARGET_HOME}/.config/labwc/autostart"
log "Configured: output=${WAYLAND_OUTPUT} transform=${ROTATE_DEG}"
log "Start now: systemctl --user start ${APP_NAME}.service"
log "Logs: journalctl --user -u ${APP_NAME}.service -f"
log "If already logged in, log out/in or restart labwc to apply rotation."