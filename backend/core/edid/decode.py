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


def edid_to_hex(edid: bytes) -> str:
    lines = []
    for i in range(0, len(edid), 16):
        chunk = edid[i:i+16]
        lines.append(
            f"{i:02X}: " + " ".join(f"{b:02X}" for b in chunk)
        )
    return "\n".join(lines)
