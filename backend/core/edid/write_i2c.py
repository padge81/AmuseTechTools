from .drm import is_connector_connected
from .i2c import find_ddc_i2c_buses
from .exceptions import EDIDWriteError
from .write import write_edid_i2c


def write_edid_for_connector(
    connector: str,
    edid: bytes,
    verify: bool = True,
    sleep: float = 0.01,
    force: bool = False,
):
    # DRM sanity check ONLY
    if not is_connector_connected(connector):
        raise EDIDWriteError(f"{connector} is not connected")

    buses = find_ddc_i2c_buses()
    if not buses:
        raise EDIDWriteError("No DDC I2C buses found")

    last_error = None

    for bus in buses:
        try:
            return write_edid_i2c(
                edid=edid,
                bus=bus,
                verify=verify,
                sleep=sleep,
                force=force,
            )
        except EDIDWriteError as e:
            last_error = e
            continue

    raise EDIDWriteError(f"All DDC buses failed: {last_error}")
    
    return {
    "connector": connector,
    "bus": bus,
    "bytes_written": 128,
    "verified": verify,
    "forced": force,
    }
