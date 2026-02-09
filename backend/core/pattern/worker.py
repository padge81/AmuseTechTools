# backend/core/pattern/worker.py

import subprocess
import signal
import threading


class PatternWorker:
    def __init__(self):
        self._lock = threading.Lock()
        self._proc = None

    def start_kmscube(self, connector_id=33):
        print("🔥 start_kmscube CALLED", connector_id, flush=True)
        with self._lock:
            self.stop()
            self._proc = subprocess.Popen(["kmscube", "-n", str(connector_id)])
)

    def stop(self):
        with self._lock:
            if self._proc:
                print("[pattern] stopping current pattern")
                self._proc.send_signal(signal.SIGINT)
                self._proc.wait(timeout=2)
                self._proc = None
