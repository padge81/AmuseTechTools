import signal
import subprocess
import threading


class PatternWorker:
    def __init__(self):
        self._lock = threading.Lock()
        self._procs = {}

    def start_kmscube(self, connector_id=33):
        with self._lock:
            self._stop_locked(connector_id)
            try:
                self._procs[connector_id] = subprocess.Popen(["kmscube", "-n", str(connector_id)])
            except FileNotFoundError as exc:
                raise RuntimeError("kmscube is not installed or not in PATH") from exc

    def stop(self, connector_id=None):
        with self._lock:
            if connector_id is None:
                for cid in list(self._procs):
                    self._stop_locked(cid)
                return

            self._stop_locked(connector_id)

    def _stop_locked(self, connector_id):
        proc = self._procs.get(connector_id)
        if not proc:
            return

        proc.send_signal(signal.SIGINT)
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()
        finally:
            self._procs.pop(connector_id, None)
