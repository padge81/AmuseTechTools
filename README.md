AmuseTechTools
A collection of tools and components designed for amusement technicians using a Raspberry Pi. This project appears to facilitate hardware interfacing, system management, and EDID (Extended Display Identification Data) handling, among other functionalities.

Table of Contents
Overview
Features
Repository Structure
Setup & Installation
Usage
Documentation
Contributing
License

--Overview
This repository provides tools and modules to support amusement systems, likely involving hardware components such as displays, card readers, coin mechanisms, ticket dispensers, and network interfaces. It includes:

	Backend logic for system control and hardware interaction
	EDID management tools for display configuration
	Web interface templates and static assets
	Scripts for setup, testing, and system configuration

--Features
	Backend System: Core logic for system management (backend/app.py, backend/core/)
	Hardware Interfaces: Modules for camera, card reader, coin mechanism, hopper, ticket dispenser, etc. (backend/routes/)
	EDID Tools: Reading, writing, comparing, and decoding EDID data (backend/core/edid/)
	System Management: Power, update, version control (backend/core/system/)
	Network & Bluetooth: Bluetooth PAN setup, USB gadget configuration (system/ scripts)
	Web UI: HTML templates and static assets for user interaction (frontend/)
	
--Repository Structure
.
├── README.md
├── AI_Prompts.txt
├── Project Design.txt
├── backend/
│   ├── __init__.py
│   ├── app.py
│   ├── config/settings.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── edid/
│   │   │   ├── __init__.py
│   │   │   ├── checksum.py
│   │   │   ├── compare.py
│   │   │   ├── decode.py
│   │   │   ├── diff.py
│   │   │   ├── exceptions.py
│   │   │   ├── i2c.py
│   │   │   ├── read.py
│   │   │   ├── save.py
│   │   │   ├── write.py
│   │   ├── system/
│   │   │   ├── power.py
│   │   │   ├── update.py
│   │   │   ├── version.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── basic_io.py
│   │   ├── camera.py
│   │   ├── card_reader.py
│   │   ├── coin_mech.py
│   │   ├── edid.py
│   │   ├── hopper.py
│   │   ├── input_output.py
│   │   ├── pattern.py
│   │   ├── system.py
│   │   ├── ticket_dispenser.py
├── edid_files/
│   ├── HDMI_EDID_Emulator.bin
│   ├── UNIS2EDID.bin
│   ├── UNIS3EDID.bin
│   └── README.md
├── frontend/
│   ├── static/
│   │   ├── css/kiosk.css
│   │   ├── images/under_construction.png
│   │   ├── js/app.js
│   └── templates/
│       ├── base.html
│       ├── basic_io.html
│       ├── camera.html
│       ├── card_reader.html
│       ├── coin_mech.html
│       ├── edid_tools.html
│       ├── hopper.html
│       ├── index.html
│       ├── input_output.html
│       ├── pattern_generator.html
│       ├── ticket_dispenser.html
├── scripts/
│   ├── install.sh
│   ├── test_edid_match.py
│   ├── test_edid_read.py
│   ├── test_edid_save.py
│   ├── test_edid_write.py
│   ├── uninstall.sh
│   └── update.sh
├── system/
│   ├── bluetooth/EnableBluetoothPAN.sh
│   ├── kiosk/setup_kiosk.sh
│   ├── kiosk/start_kiosk.sh
│   └── usb/setup_usb_gadget.sh

--Setup & Installation
	Clone the repository:
	git clone <repository_url>
	Navigate into the project directory:
	cd AmuseTechTools
	Install dependencies listed in backend/requirements.txt:
	pip install -r backend/requirements.txt
	Follow any additional setup instructions in system/ scripts or documentation files.

	One-step Raspberry Pi kiosk installer (dependencies + service + rotation/cursor controls):
	scripts/install.sh

	This installs required apt packages, creates a venv, installs Python deps, writes
	user + system services named `amuse-tech-tools.service`, configures touchscreen/display
	rotation, locks kiosk to the chosen display output, creates a Desktop launcher, and
	enables boot autostart.

--Usage
	To run the backend server, typically:
	python backend/app.py
	Use the web interface by navigating to the server URL (e.g., http://localhost:5000) after starting the backend.

	Scripts in scripts/ can be used for testing EDID functionalities:

	python scripts/test_edid_read.py
	System setup scripts (e.g., setup_kiosk.sh) are for configuring the Raspberry Pi environment.

	Pattern generator Pi safety setup (one-time):

	sudo scripts/setup_pattern_pi_once.sh <your-app-service-name>

	This writes `/etc/default/amuse-tech-tools-pattern` and a matching systemd override so
	`DSI-1` remains protected while pattern output can be targeted to HDMI connectors.
--Documentation
	For detailed architecture and component explanations, refer to docs/architecture.md and other markdown files.
	EDID handling is documented in docs/edid.md.
	Bluetooth setup is described in docs/bluetooth.md.
	For kiosk-specific configurations, see docs/kiosk.md.

--Contributing
	Contributions are welcome! Please fork the repository, create a feature branch, and submit a pull request with your improvements.

