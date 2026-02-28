# INSTALL.md

# AmuseTechTools Installation Guide

This document provides step-by-step instructions to install and run AmuseTechTools as a kiosk appliance on a Raspberry Pi.

This setup is designed for:

- Raspberry Pi OS / Debian 13 (Trixie)
- LightDM display manager
- labwc (Wayland compositor)
- Chromium kiosk mode
- Official Raspberry Pi DSI touchscreen (optional but supported)

---

# 1. Prepare Raspberry Pi

## Recommended OS

Install:

**Raspberry Pi OS (Desktop) – Debian 13 (Trixie)**

Ensure the system is updated:

~~~bash
sudo apt update
sudo apt upgrade -y
~~~

Reboot if required:

~~~bash
sudo reboot
~~~

---

# 2. Clone Repository

Open a terminal and run:

~~~bash
git clone https://github.com/padge81/AmuseTechTools.git
cd AmuseTechTools
~~~

---

# 3. Run Installer

Make installer executable:

~~~bash
chmod +x scripts/install.sh
~~~

Run installer:

~~~bash
sudo ./scripts/install.sh
~~~

---

# Optional: Set Screen Rotation During Install

If using the official DSI display and needing rotation:

~~~bash
sudo ROTATE_DEG=270 WAYLAND_OUTPUT=DSI-1 ./scripts/install.sh
~~~

Valid values for ROTATE_DEG:

- 0
- 90
- 180
- 270

---

# 4. Reboot

~~~bash
sudo reboot
~~~

After reboot, the kiosk should start automatically.

---

# What The Installer Configures

The installer automatically:

• Installs system dependencies:
  - chromium / chromium-browser
  - python3
  - python3-venv
  - python3-smbus
  - wlr-randr
  - unclutter
  - wmctrl
  - xdotool
  - curl

• Creates a Python virtual environment:

~~~bash
python3 -m venv --system-site-packages .venv
~~~

This allows access to system hardware modules like:

~~~python
from smbus import SMBus
~~~

• Installs backend requirements from:
  backend/requirements.txt

• Configures Wayland screen rotation via:

~~~bash
~/.config/labwc/autostart
~~~

• Creates kiosk startup script:
  system/kiosk/start_kiosk.sh

• Installs and enables systemd user service:
  amuse-tech-tools.service

• Enables boot autostart using loginctl linger

• Creates Desktop launcher

---

# Service Management

Service name:

amuse-tech-tools.service

Check status:

~~~bash
systemctl --user status amuse-tech-tools.service --no-pager -l
~~~

Restart service:

~~~bash
systemctl --user restart amuse-tech-tools.service
~~~

View kiosk log:

~~~bash
tail -n 200 ~/amuse-tech-tools-kiosk.log
~~~

---

# Display Configuration (Wayland)

Rotation is handled by Wayland using wlr-randr.

Example configuration inside:

~/.config/labwc/autostart

~~~bash
wlr-randr --output DSI-1 --pos 0,0 --transform 270
~~~

Do NOT use:

- xrandr
- xinput
- config.txt lcd_rotate
- cmdline video=rotate

Wayland controls output transforms.

---

# HDMI vs DSI Output Behavior

Chromium opens on the display positioned at (0,0).

If Chromium opens on HDMI instead of DSI:

Disable HDMI:

~~~bash
wlr-randr --output DSI-1 --pos 0,0 --transform 270
wlr-randr --output HDMI-A-1 --off
~~~

Or move HDMI to the right:

~~~bash
wlr-randr --output DSI-1 --pos 0,0 --transform 270
wlr-randr --output HDMI-A-1 --pos 800,0 --transform normal
~~~

Check display names:

~~~bash
wlr-randr
~~~

---

# Updating The Appliance

To update from GitHub:

~~~bash
cd ~/AmuseTechTools
git pull
sudo ./scripts/install.sh
sudo reboot
~~~

Do not manually modify files on the device. All changes should be committed to the repository.

---

# Troubleshooting

## Backend not loading

Check:

~~~bash
tail -n 200 ~/amuse-tech-tools-kiosk.log
~~~

## smbus Module Error

Ensure installer created venv with:

--system-site-packages

Re-run installer if necessary.

## Service Restart Loop

Common causes:

- Python import error
- App factory not called properly
- Missing dependency

Logs will show the exact error.

---

# Deployment Philosophy

This system is intended to behave as a deterministic appliance:

- No manual modifications on device
- All changes committed to repository
- Installer configures full environment
- Systemd controls lifecycle
- Wayland controls display
- System packages handle hardware access

---

Installation complete.