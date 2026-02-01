import time
from backend.core.pattern.state import get_state
from backend.core.pattern.output import output_solid_color

_active_output = None
_active_color = None

def pattern_worker():
    global _active_output, _active_color

    print("Pattern worker started")

    while True:
        state = get_state()

        if not state["active"]:
            time.sleep(0.1)
            continue

        # Only reconfigure if something changed
        if (
            state["mode"] == "solid" and
            (state["output"] != _active_output or state["value"] != _active_color)
        ):
            output_solid_color(state["output"], state["value"])
            _active_output = state["output"]
            _active_color = state["value"]

        time.sleep(0.05)