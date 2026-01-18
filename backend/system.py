import subprocess
from pathlib import Path

VERSION_FILE = Path("VERSION")

def get_version():
    if VERSION_FILE.exists():
        return VERSION_FILE.read_text().strip()
    return "unknown"

def system_action(action):
    if action == "reboot":
        subprocess.Popen(["sudo", "reboot"])
    elif action == "shutdown":
        subprocess.Popen(["sudo", "shutdown", "-h", "now"])
    elif action == "exit_browser":
        subprocess.Popen(["pkill", "chromium"])
    elif action == "update":
        subprocess.Popen(["git", "pull"])
    else:
        return {"status": "error", "message": "Unknown action"}

    return {"status": "ok"}
