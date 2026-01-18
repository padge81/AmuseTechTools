import os
import subprocess


def system_action(action: str):
    if action == "reboot":
        subprocess.run(["sudo", "reboot"], check=False)

    elif action == "shutdown":
        subprocess.run(["sudo", "shutdown", "-h", "now"], check=False)

    elif action == "exit_browser":
        # Kill Chromium (kiosk mode)
        subprocess.run(["pkill", "-f", "chromium"], check=False)

    elif action == "update":
        subprocess.run(
            ["git", "-C", "/home/att/AmuseTechTools", "pull"],
            check=False
        )

    else:
        raise ValueError(f"Unknown system action: {action}")


def get_version():
    try:
        result = subprocess.check_output(
            ["git", "-C", "/home/att/AmuseTechTools", "describe", "--tags", "--dirty"],
            stderr=subprocess.DEVNULL
        )
        return result.decode().strip()
    except Exception:
        return "unknown"
