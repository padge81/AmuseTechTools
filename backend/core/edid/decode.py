import subprocess
import tempfile
from pathlib import Path






def decode_basic(edid: bytes) -> dict:
    mfg_id = (edid[8] << 8) | edid[9]
    manufacturer = "".join(
        chr(((mfg_id >> shift) & 0x1F) + 64)
        for shift in (10, 5, 0)
    )

    return {
        "manufacturer": manufacturer,
        "product_code": edid[10] | (edid[11] << 8),
        "serial": int.from_bytes(edid[12:16], "little"),
        "week": edid[16],
        "year": 1990 + edid[17],
        "extensions": edid[126],
    }


def edid_to_hex(edid: bytes, width: int = 16) -> str:
    """
    Convert EDID bytes to formatted hex string.
    """
    lines = []
    for i in range(0, len(edid), width):
        chunk = edid[i:i + width]
        line = " ".join(f"{b:02x}" for b in chunk)
        lines.append(line)
    return "\n".join(lines)

def decode_full_text(edid: bytes) -> str:
    """
    Decode EDID using system edid-decode tool.
    Returns full human-readable text.
    """
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(edid)
        temp_path = f.name

    try:
        result = subprocess.run(
            ["edid-decode", temp_path],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip())

        return result.stdout
    finally:
        Path(temp_path).unlink(missing_ok=True)