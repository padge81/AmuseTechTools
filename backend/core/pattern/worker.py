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
            self._preflight(cmd)

            try:
                self._procs[connector_id] = subprocess.Popen(
                    cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
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

    def _preflight(self, cmd):
        try:
            result = subprocess.run(
                cmd + ["-c", "1"],
                check=False,
                capture_output=True,
                text=True,
                timeout=8,
            )
        except FileNotFoundError as exc:
            raise RuntimeError("kmscube is not installed or not in PATH") from exc
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError("kmscube preflight timed out") from exc

        if result.returncode == 0:
            return

        output = ((result.stdout or "") + "\n" + (result.stderr or "")).strip()
        lowered = output.lower()

        if "permission denied" in lowered or "failed to set mode" in lowered:
            raise RuntimeError(
                "kmscube failed to acquire DRM mode-setting access (permission denied). "
                "Ensure display manager/compositor is stopped and user has DRM permissions."
            )

        first_line = output.splitlines()[0] if output else f"exit code {result.returncode}"
        raise RuntimeError(f"kmscube preflight failed: {first_line}")

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
