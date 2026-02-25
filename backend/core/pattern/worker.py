import signal
import subprocess
import threading


class PatternWorker:
    def __init__(self):
        self._lock = threading.Lock()
        self._procs = {}
        self._supports_connector_arg = None

    def start_kmscube(self, connector_id=33):
        with self._lock:
            self._stop_locked(connector_id)

            cmd = self._kmscube_command(connector_id)
            try:
                self._procs[connector_id] = subprocess.Popen(cmd)
            except FileNotFoundError as exc:
                raise RuntimeError("kmscube is not installed or not in PATH") from exc

            return {
                "connector_id": connector_id,
                "command": cmd,
                "connector_selection_supported": self._supports_connector_arg,
            }

    def stop(self, connector_id=None):
        with self._lock:
            if connector_id is None:
                for cid in list(self._procs):
                    self._stop_locked(cid)
                return

            self._stop_locked(connector_id)

    def _kmscube_command(self, connector_id):
        if self._supports_connector_arg is None:
            self._supports_connector_arg = self._detect_connector_arg_support()

        if self._supports_connector_arg:
            return ["kmscube", "-n", str(connector_id)]

        return ["kmscube"]

    @staticmethod
    def _detect_connector_arg_support():
        try:
            help_result = subprocess.run(
                ["kmscube", "--help"],
                check=False,
                capture_output=True,
                text=True,
            )
        except FileNotFoundError:
            return False

        combined = (help_result.stdout or "") + (help_result.stderr or "")
        return "-n" in combined or "--connector" in combined

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
