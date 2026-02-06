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
def normalize(name: str) -> str:
    return name.replace("card0-", "").lower()

def find_connector(card, requested_name):
    req = normalize(requested_name)

    for conn_id in range(0, 32):
        try:
            conn = pykms.Connector(card, conn_id)
        except Exception:
            continue

        try:
            full = normalize(conn.fullname)
            if req in full and conn.connected():
                print(f"[DRM] Matched connector: {conn.fullname}")
                return conn
        except Exception:
            continue

    raise RuntimeError(f"Connector {requested_name} not found or not connected")

#---------------------------------------
# Pick a Mode
#---------------------------------------
def pick_mode(connector):
    if not connector.modes:
        raise RuntimeError("No modes available")
    return connector.modes[0]
    
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
    # Find a working encoder
    enc = None
    for enc_id in range(0, 8):
        try:
            e = pykms.Encoder(card, enc_id)
        except Exception:
            continue

        if e.id in connector.encoders:
            enc = e
            break

    if not enc:
        raise RuntimeError("No encoder found for connector")

    crtc = pykms.Crtc(card, enc.crtcs[0])

    pykms.AtomicReq(card) \
        .add_connector(connector, crtc, fb) \
        .add_crtc(crtc, fb, mode) \
        .commit_sync()
        
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

