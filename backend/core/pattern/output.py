import pykms
import mmap

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
    stride = mode.hdisplay * 4
    size = stride * mode.vdisplay

    buf = pykms.DumbFramebuffer(
        card,
        mode.hdisplay,
        mode.vdisplay,
        pykms.PixelFormat.XRGB8888
    )

    mm = mmap.mmap(
        buf.fd,
        size,
        mmap.MAP_SHARED,
        mmap.PROT_WRITE | mmap.PROT_READ
    )

    return buf, mm
    
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

    r, g, b = colors[color]
    pixel = bytes([b, g, r, 0])  # XRGB

    mm.seek(0)
    mm.write(pixel * (width * height))
    
#---------------------------------------
# Modeset (this makes it visible)
#---------------------------------------
def modeset(card, connector, mode, fb):
    crtc = connector.encoders[0].crtcs[0]

    req = pykms.AtomicReq(card)
    req.add_connector(connector, crtc, fb)
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

