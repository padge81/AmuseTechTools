# backend/core/pattern/output.py

import subprocess
import signal

class PatternOutput:
    def __init__(self):
        self.process = None

    def stop(self):
        if self.process:
            try:
                self.process.send_signal(signal.SIGTERM)
                self.process.wait(timeout=2)
            except Exception:
                self.process.kill()
            finally:
                self.process = None

    def start_solid(self, connector_id, mode, color):
        """
        Example:
        modetest -M vc4 -a -s 33@0:1280x720 -F solid-red
        """
        self.stop()

        cmd = [
            "modetest",
            "-M", "vc4",
            "-a",
            "-s", f"{connector_id}@0:{mode}",
            "-F", f"solid-{color}",
        ]

        self.process = subprocess.Popen(cmd)


    def off(self):
        self.stop()

