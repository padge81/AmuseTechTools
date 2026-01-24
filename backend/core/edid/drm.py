from pathlib import Path
from backend.core.edid.exceptions import EDIDWriteError

SYS_DRM = Path("/sys/class/drm")
DEV_I2C = Path("/dev")


def resolve_connector_i2c(connector: str) -> int:
    """
    Resolve DRM connector (e.g. HDMI-A-1) to its DDC I2C bus number.
    """

    if not connector:
        raise EDIDWriteError("No DRM connector specified")

    matches = list(SYS_DRM.glob(f"*-{connector}"))

    if not matches:
        raise EDIDWriteError(f"DRM connector '{connector}' not found")

    if len(matches) > 1:
        raise EDIDWriteError(f"Ambiguous DRM connector '{connector}'")

    drm_path = matches[0]
    ddc_path = drm_path / "ddc"

    if not ddc_path.exists():
        raise EDIDWriteError(f"No DDC directory for {connector}")

    i2c_dirs = []

    for p in ddc_path.iterdir():
        if not p.name.startswith("i2c-"):
            continue

        suffix = p.name.removeprefix("i2c-")
        if suffix.isdigit():
            i2c_dirs.append(p)

    if not i2c_dirs:
        raise EDIDWriteError(f"No I2C bus found for {connector}")

    if len(i2c_dirs) > 1:
        raise EDIDWriteError(f"Multiple I2C buses found for {connector}")

    bus = int(i2c_dirs[0].name.split("-")[1])

    if not (DEV_I2C / f"i2c-{bus}").exists():
        raise EDIDWriteError(f"/dev/i2c-{bus} does not exist")

    return bus
