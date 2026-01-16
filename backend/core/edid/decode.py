def decode_edid(edid: bytes) -> str:
    lines = []

    mfg_id = ((edid[8] & 0x7C) >> 2) + 64
    mfg_id += chr(((edid[8] & 0x03) << 3 | (edid[9] & 0xE0) >> 5) + 64)
    mfg_id += chr((edid[9] & 0x1F) + 64)

    product_code = edid[10] | (edid[11] << 8)
    serial = int.from_bytes(edid[12:16], "little")

    lines.append(f"Manufacturer: {mfg_id}")
    lines.append(f"Product Code: {product_code}")
    lines.append(f"Serial: {serial}")
    lines.append(f"EDID Version: {edid[18]}.{edid[19]}")

    return "\n".join(lines)
