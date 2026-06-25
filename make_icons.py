#!/usr/bin/env python3
"""Generate PNG icons for the PWA using only the standard library."""
import zlib, struct, math

# Brand palette
BG = (15, 118, 110)      # teal-700
DROP = (240, 253, 250)   # mint-50
ACCENT = (45, 212, 191)  # teal-300


def png(width, height, pixels):
    """pixels: list of (r,g,b,a) rows*cols, return PNG bytes."""
    raw = bytearray()
    for y in range(height):
        raw.append(0)  # filter type 0
        for x in range(width):
            r, g, b, a = pixels[y * width + x]
            raw += bytes((r, g, b, a))

    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        c += struct.pack(">I", zlib.crc32(tag + data) & 0xffffffff)
        return c

    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    idat = zlib.compress(bytes(raw), 9)
    return sig + chunk(b"IHDR", ihdr) + chunk(b"IDAT", idat) + chunk(b"IEND", b"")


def draw(size):
    px = [(0, 0, 0, 0)] * (size * size)
    radius = size * 0.22          # rounded-corner radius
    cx, cy = size / 2, size / 2

    def rounded_alpha(x, y):
        # distance into rounded-rect corners for anti-aliased edge
        dx = max(radius - x, x - (size - radius), 0)
        dy = max(radius - y, y - (size - radius), 0)
        d = math.hypot(dx, dy)
        return max(0.0, min(1.0, radius - d + 0.5))

    # Droplet geometry: teardrop = circle bottom + triangle top
    dr = size * 0.20             # droplet circle radius
    dcx, dcy = cx, cy + size * 0.10
    tip_y = cy - size * 0.26

    for y in range(size):
        for x in range(size):
            i = y * size + x
            ra = rounded_alpha(x + 0.5, y + 0.5)
            if ra <= 0:
                continue
            r, g, b = BG

            # droplet body (lower circle)
            ddx, ddy = (x + 0.5) - dcx, (y + 0.5) - dcy
            in_circle = math.hypot(ddx, ddy) <= dr
            # droplet point (triangle narrowing to tip)
            in_point = False
            if tip_y <= (y + 0.5) <= dcy:
                t = ((y + 0.5) - tip_y) / (dcy - tip_y)
                halfw = dr * t
                if abs((x + 0.5) - dcx) <= halfw:
                    in_point = True
            if in_circle or in_point:
                r, g, b = DROP
                # subtle highlight on the droplet
                if math.hypot(ddx + dr * 0.3, ddy + dr * 0.3) <= dr * 0.35:
                    r, g, b = (255, 255, 255)

            a = int(255 * ra)
            px[i] = (r, g, b, a)
    return px


for size in (192, 512, 180):
    data = png(size, size, draw(size))
    name = "icons/apple-touch-icon.png" if size == 180 else f"icons/icon-{size}.png"
    with open(name, "wb") as f:
        f.write(data)
    print("wrote", name, len(data), "bytes")
