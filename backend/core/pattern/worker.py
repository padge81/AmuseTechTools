import shutil
import signal
import subprocess
import threading


class PatternWorker:
    def __init__(self):
        self._lock = threading.Lock()
        self._procs = {}
        self._has_gstreamer = None

    def start_solid_color(self, connector_id, color_hex="#ffffff"):
        color = self._hex_to_uint32(color_hex)
        cmd = [
            "gst-launch-1.0",
            "-q",
            "videotestsrc",
            "is-live=true",
            "pattern=solid-color",
            f"foreground-color={color}",
            "!",
            "video/x-raw,framerate=30/1",
            "!",
            "kmssink",
            f"connector-id={connector_id}",
            "sync=false",
        ]
        self._start(connector_id, cmd)

    def start_colorbars(self, connector_id):
        cmd = [
            "gst-launch-1.0",
            "-q",
            "videotestsrc",
            "is-live=true",
            "pattern=smpte",
            "!",
            "video/x-raw,framerate=30/1",
            "!",
            "kmssink",
            f"connector-id={connector_id}",
            "sync=false",
        ]
        self._start(connector_id, cmd)

    def stop(self, connector_id=None):
        with self._lock:
            if connector_id is None:
                for cid in list(self._procs):
                    self._stop_locked(cid)
                return
            self._stop_locked(connector_id)

    def _start(self, connector_id, cmd):
        with self._lock:
            self._ensure_gstreamer_available()
            self._stop_locked(connector_id)
            try:
                self._procs[connector_id] = subprocess.Popen(
                    cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            except FileNotFoundError as exc:
                raise RuntimeError("gst-launch-1.0 is not installed or not in PATH") from exc

    def _ensure_gstreamer_available(self):
        if self._has_gstreamer is None:
            self._has_gstreamer = bool(shutil.which("gst-launch-1.0"))
        if not self._has_gstreamer:
            raise RuntimeError("GStreamer is not available (gst-launch-1.0 not found)")

    @staticmethod
    def _hex_to_uint32(color_hex):
        color = (color_hex or "#ffffff").strip().lstrip("#")
        if len(color) != 6:
            color = "ffffff"
        try:
            rgb = int(color, 16)
        except ValueError:
            rgb = 0xFFFFFF

        # ARGB expected by videotestsrc foreground-color
        return (0xFF << 24) | rgb

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
