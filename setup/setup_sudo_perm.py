#!/usr/bin/env python3

import os
import sys
import subprocess
import getpass
from pathlib import Path

SUDOERS_DIR = Path("/etc/sudoers.d")
SUDOERS_FILE = SUDOERS_DIR / "amusetools"

ALLOWED_COMMANDS = [
    "/sbin/reboot",
    "/sbin/shutdown",
    "/usr/bin/systemctl",
    "/usr/bin/git",
    "/usr/bin/pkill",
]

def require_root():
    if os.geteuid() != 0:
        print("❌ This script must be run with sudo")
        sys.exit(1)

def build_sudoers_entry(user: str) -> str:
    commands = ", ".join(ALLOWED_COMMANDS)
    return f"{user} ALL=(ALL) NOPASSWD: {commands}\n"

def validate_sudoers():
    result = subprocess.run(
        ["visudo", "-cf", "/etc/sudoers"],
        capture_output=True,
        text=True
    )
    return result.returncode == 0, result.stderr

def main():
    require_root()

    user = getpass.getuser()
    print(f"✔ Configuring sudo permissions for user: {user}")

    entry = build_sudoers_entry(user)

    if SUDOERS_FILE.exists():
        existing = SUDOERS_FILE.read_text()
        if entry.strip() in existing:
            print("✔ Sudo permissions already configured")
            return

    print("✍ Writing sudoers file...")
    SUDOERS_FILE.write_text(entry)
    os.chmod(SUDOERS_FILE, 0o440)

    print("🔍 Validating sudoers...")
    ok, error = validate_sudoers()
    if not ok:
        print("❌ sudoers validation failed!")
        print(error)
        print("⚠ Rolling back changes")
        SUDOERS_FILE.unlink(missing_ok=True)
        sys.exit(1)

    print("✔ Sudo permissions successfully installed")

if __name__ == "__main__":
    main()
