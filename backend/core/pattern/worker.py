import time

from backend.core.pattern.state import get_state
from backend.core.pattern import output

_active_mode = None
_active_output = None
_active_value = None


def pattern_worker():
    global _active_mode, _active_output, _active_value

    print("Pattern worker started")

    while True:
        state = get_state()

        # ---------------------------------
        # Inactive → ensure output stopped
        # ---------------------------------
        if not state.get("active", False):
            if _active_mode is not None:
                output.stop_current()
                _active_mode = None
                _active_output = None
                _active_value = None

            time.sleep(0.1)
            continue

        mode = state.get("mode")
        output_name = state.get("output")
        value = state.get("value")

        # ---------------------------------
        # SOLID COLOUR
        # ---------------------------------
        if mode == "solid":
            if (
                _active_mode != "solid"
                or _active_output != output_name
                or _active_value != value
            ):
                output.solid_color(output_name, value)
                _active_mode = "solid"
                _active_output = output_name
                _active_value = value

        # ---------------------------------
        # SCREENSAVER
        # ---------------------------------
        elif mode == "screensaver":
            if _active_mode != "screensaver":
                output.screensaver()
                _active_mode = "screensaver"
                _active_output = None
                _active_value = None

        # ---------------------------------
        # OFF / UNKNOWN
        # ---------------------------------
        else:
            if _active_mode is not None:
                output.stop_current()
                _active_mode = None
                _active_output = None
                _active_value = None

        time.sleep(0.05)
