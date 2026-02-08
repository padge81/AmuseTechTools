# backend/core/pattern/worker.py

import subprocess
import signal
import threading


class PatternWorker:
    def __init__(self):
        self._lock = threading.Lock()
        self._proc = None

    def start_kmscube(self, connector_id=33):
        with self._lock:
            self.stop()

            print("[pattern] starting kmscube")

            self._proc = subprocess.Popen(
                ["kmscube", "-n", str(connector_id)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

    def stop(self):
        with self._lock:
            if self._proc:
                print("[pattern] stopping current pattern")
                self._proc.send_signal(signal.SIGINT)
                self._proc.wait(timeout=2)
                self._proc = None
