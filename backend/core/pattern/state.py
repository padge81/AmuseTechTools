
import threading
from copy import deepcopy

class PatternState:
    def __init__(self):
        self._lock = threading.Lock()
        self._state = {
            "output": None,        # connector id (int)
            "mode": "off",         # off | solid | screensaver
            "value": None,         # e.g. "red"
            "active": False,       # display ownership taken
        }

    def get(self):
        with self._lock:
            return deepcopy(self._state)

    def update(self, **kwargs):
        with self._lock:
            changed = False
            for k, v in kwargs.items():
                if self._state.get(k) != v:
                    self._state[k] = v
                    changed = True
            return changed