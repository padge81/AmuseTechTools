from .drm import is_connector_connected
from .i2c import find_ddc_i2c_buses
from .exceptions import EDIDWriteError
from .write import write_edid_i2c


def write_edid_for_connector(
    connector: str,
    edid: bytes,
    verify: bool = True,
    force: bool = False,
):
    # 1. Validate connector via DRM
    if not is_connector_connected(connector):
        raise EDIDWriteError(
            f"Connector {connector} is not connected"
        )

    # 2. Find writable DDC I2C buses
    buses = find_ddc_i2c_buses()
    if not buses:
        raise EDIDWriteError("No DDC I2C buses detected")

    last_error = None

    # 3. Try buses until one works
    for bus in buses:
        try:
            return write_edid_i2c(
                edid=edid,
                bus=bus,
                verify=verify,
                force=force,
            )
        except Exception as e:
            last_error = e

    raise EDIDWriteError(
        f"All DDC buses failed: {last_error}"
    )
