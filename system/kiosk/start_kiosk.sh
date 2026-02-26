#!/usr/bin/env bash
set -euo pipefail

APP_NAME="amuse-tech-tools"

systemctl --user start "${APP_NAME}.service"
systemctl --user --no-pager --full status "${APP_NAME}.service" | sed -n '1,20p'
