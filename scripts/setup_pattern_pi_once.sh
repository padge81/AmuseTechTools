#!/usr/bin/env bash
set -euo pipefail

# One-time setup for Raspberry Pi pattern safety:
# - Keep UI connector protected (default: DSI-1)
# - Disable global DRM takeover by default
# - Wire env file into a systemd override for the app service
#
# Usage:
#   sudo scripts/setup_pattern_pi_once.sh [service_name]
# Example:
#   sudo scripts/setup_pattern_pi_once.sh amuse-tech-tools

SERVICE_NAME="${1:-amuse-tech-tools}"
ENV_FILE="/etc/default/amuse-tech-tools-pattern"
OVERRIDE_DIR="/etc/systemd/system/${SERVICE_NAME}.service.d"
OVERRIDE_FILE="${OVERRIDE_DIR}/10-pattern-pi-safe.conf"

if [[ "${EUID}" -ne 0 ]]; then
  echo "This script must be run as root (use sudo)." >&2
  exit 1
fi

echo "[1/4] Writing ${ENV_FILE}"
cat > "${ENV_FILE}" <<'ENVVARS'
# Pattern safety defaults for Raspberry Pi dual-screen setup
# UI panel remains on DSI-1 while pattern output can target HDMI.
PATTERN_FORCE_GLOBAL_DRM_CONTROL=0
PATTERN_ALLOW_GLOBAL_DRM_CONTROL=0
PATTERN_PROTECTED_CONNECTORS=DSI-1
ENVVARS

chmod 0644 "${ENV_FILE}"

echo "[2/4] Writing systemd override ${OVERRIDE_FILE}"
mkdir -p "${OVERRIDE_DIR}"
cat > "${OVERRIDE_FILE}" <<EOF2
[Service]
EnvironmentFile=${ENV_FILE}
EOF2

chmod 0644 "${OVERRIDE_FILE}"

echo "[3/4] Reloading systemd and restarting ${SERVICE_NAME}.service"
systemctl daemon-reload
systemctl restart "${SERVICE_NAME}.service"

echo "[4/4] Showing service status"
systemctl --no-pager --full status "${SERVICE_NAME}.service" | sed -n '1,20p'

echo
echo "Done. Applied safe pattern settings:"
echo "  PATTERN_FORCE_GLOBAL_DRM_CONTROL=0"
echo "  PATTERN_ALLOW_GLOBAL_DRM_CONTROL=0"
echo "  PATTERN_PROTECTED_CONNECTORS=DSI-1"
echo
echo "Tip: verify API capabilities once the app is up:"
echo "  curl -s http://127.0.0.1:8080/pattern/capabilities | python3 -m json.tool"
