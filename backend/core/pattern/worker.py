import time
from pattern.state import get_state
from backend.core.pattern.output import output_solid_color

def pattern_worker():
    """
    Long-running worker loop.
    Eventually owns DRM, framebuffer, vsync.
    """
    print("Pattern worker started")
    while True:
        state = get_state()

        if not state["active"]:
            time.sleep(0.1)
            continue

        if state["mode"] == "solid":
            render_solid_color(state["value"])

        elif state["mode"] == "pattern":
            render_test_pattern(state["value"])

        elif state["mode"] == "saver":
            render_screen_saver()

        time.sleep(0.016)  # ~60Hz placeholder
        
def render_solid_color(color):
    state = get_state()
    output_solid_color(state["output"], color)