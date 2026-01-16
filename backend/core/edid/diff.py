def diff_edid(expected: bytes, actual: bytes) -> str:
    out = []

    for i, (a, b) in enumerate(zip(expected, actual)):
        if a != b:
            out.append(f"0x{i:02X}: {a:02X} != {b:02X}")

    return "\n".join(out)
