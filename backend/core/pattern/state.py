from threading import Lock

_state = {
    "output": None,        # HDMI-A-1
    "mode": None,          # solid | pattern | saver
    "value": None,         # green | smpte | logo
    "active": False
}

_lock = Lock()

def set_state(**kwargs):
    with _lock:
        _state.update(kwargs)

def get_state():
    with _lock:
        return dict(_state)
