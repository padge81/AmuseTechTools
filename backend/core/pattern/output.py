import pykms
#import mmap

#---------------------------------------
# Open DRM Card
#---------------------------------------
def open_card():
    return pykms.Card()

#---------------------------------------
# Find Connector By Name
#--------------------------------------- 
def find_connector(card, requested_name):
    for conn in card.connectors:
        if conn.fullname == requested_name and conn.connected():
            return conn
    raise RuntimeError(f"Connector {requested_name} not found or not connected")

#---------------------------------------
# Pick a Mode
#---------------------------------------
def pick_mode(connector):
    modes = connector.get_modes()
    if not modes:
        raise RuntimeError("No display modes available")
    return modes[0]  # preferred / first mode
    
#---------------------------------------
# Create framebuffer + mmap
#---------------------------------------
def create_fb(card, mode):
    fb = pykms.DumbFramebuffer(
        card,
        mode.hdisplay,
        mode.vdisplay,
        pykms.PixelFormat.XRGB8888
    )

    mm = fb.map(0)   # 👈 REQUIRED offset

    return fb, mm
    
#---------------------------------------
# Fill Framebuffer with solid colour
#---------------------------------------
def fill_color(mm, width, height, color):
    colors = {
        "red":   (255, 0, 0),
        "green": (0, 255, 0),
        "blue":  (0, 0, 255),
        "black": (0, 0, 0),
        "white": (255, 255, 255),
    }

    if color not in colors:
        raise ValueError(f"Unknown color: {color}")

    r, g, b = colors[color]
    pixel = bytes([b, g, r, 0])  # XRGB8888

    mv = mm.cast("B")            # 🔥 flatten memoryview
    mv[:] = pixel * (width * height)
    
#---------------------------------------
# Modeset (this makes it visible)
#---------------------------------------
def modeset(card, connector, mode, fb):
    res = pykms.ResourceManager(card)

    crtc = res.reserve_crtc(connector)
    if not crtc:
        raise RuntimeError("Failed to reserve CRTC")

    req = pykms.AtomicReq(card)
    req.add_connector(connector, crtc)
    req.add_crtc(crtc, fb, mode)
    req.commit_sync()
        
#---------------------------------------
# High-level entry function (what worker calls)
#---------------------------------------
def output_solid_color(connector_name, color):
    card = open_card()
    connector = find_connector(card, connector_name)
    mode = pick_mode(connector)

    fb, mm = create_fb(card, mode)
    fill_color(mm, mode.hdisplay, mode.vdisplay, color)
    modeset(card, connector, mode, fb)

