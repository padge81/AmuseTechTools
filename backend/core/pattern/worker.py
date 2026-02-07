# backend/core/pattern/worker.py

import time
import subprocess
from .output import PatternOutput

class PatternWorker(threading.Thread):
    def __init__(self, state):
        super().__init__(daemon=True)
        self.state = state
        self.output = PatternOutput()
        self._last_state = None

    def run(self):
        while True:
            current = self.state.get()

            if current != self._last_state:
                self.apply(current)
                self._last_state = current

            time.sleep(0.2)

    def apply(self, state):
        if not state["active"]:
            self.output.off()
            return

        if state["mode"] == "solid":
            if state["output"] and state["value"]:
                # Hardcode a known-good mode for now
                self.output.start_solid(
                    connector_id=state["output"],
                    mode="1280x720",
                    color=state["value"],
                )
        else:
            self.output.off()
