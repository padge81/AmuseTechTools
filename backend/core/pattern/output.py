import subprocess
import signal
import time
from typing import Optional

# Track the currently running pattern process
_current_process: Optional[subprocess.Popen] = None


# -------------------------------------------------
# Process control helpers
# -------------------------------------------------

def start_command(cmd: list[str]):
    """
    Stop any existing pattern process and start a new one.
    """
    global _current_process

    stop_current()

    _current_process = subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True  # ensures clean signal handling
    )


def stop_current():
    """
    Stop the currently running pattern process (if any).
    """
    global _current_process

    if not _current_process:
        return

    try:
        _current_process.send_signal(signal.SIGTERM)
        _current_process.wait(timeout=1)
    except Exception:
        # Force kill if it refuses to die
        try:
            _current_process.kill()
        except Exception:
            pass

    _current_process = None


# -------------------------------------------------
# Pattern commands
# -------------------------------------------------

def solid_color(output: str, color: str):
    """
    Display a solid colour using modetest.

    `output` is a DRM connector name (e.g. HDMI-A-1, DSI-1)
    `color` is a modetest colour name (red, green, blue, white, black)
    """

    # modetest requires a full mode string; we let it auto-pick the preferred mode
    cmd = [
        "modetest",
        "-M", "vc4",
        "-s", f"{output}@0:{color}"
    ]

    start_command(cmd)


def screensaver():
    """
    Simple screensaver / blanking mode.
    Implemented as an external script so it can evolve independently.
    """

    start_command([
        "/usr/local/bin/screensaver.sh"
    ])


# -------------------------------------------------
# Emergency cleanup (used on release / shutdown)
# -------------------------------------------------

def shutdown():
    """
    Hard stop all output activity.
    """
    stop_current()
