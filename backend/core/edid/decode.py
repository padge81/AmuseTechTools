import subprocess
import tempfile
from pathlib import Path

def decode_edid_text(edid: bytes) -> str:
    """
    Decode EDID using edid-decode if available.
    Returns full human-readable text.
    """

    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(edid)
        temp_path = f.name

    try:
        result = subprocess.run(
            ["edid-decode", temp_path],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    finally:
        Path(temp_path).unlink(missing_ok=True)
