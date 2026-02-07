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
        self.stop()

        cmd = ["kmscube"]
        self.process = subprocess.Popen(cmd)


    def off(self):
        self.stop()

