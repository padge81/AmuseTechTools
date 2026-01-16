def diff_edid(a: bytes, b: bytes) -> str:
    diffs = []
    for i, (x, y) in enumerate(zip(a, b)):
        if x != y:
            diffs.append(f"0x{i:02X}: {x:02X} != {y:02X}")
    return "\n".join(diffs)
