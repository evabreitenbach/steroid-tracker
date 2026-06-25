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


def _in_rounded_rect(u, v, x0, y0, x1, y1, r):
    if u < x0 or u > x1 or v < y0 or v > y1:
        return False
    dx = max(x0 + r - u, u - (x1 - r), 0.0)
    dy = max(y0 + r - v, v - (y1 - r), 0.0)
    return dx * dx + dy * dy <= r * r


def diaper_region(u, v):
    """Classify a point in unit-square coords: 0 none, 1 fabric, 2 waistband."""
    # Body: a wide rounded brief filling the top, before leg cutouts.
    if not _in_rounded_rect(u, v, 0.15, 0.26, 0.85, 0.73, 0.11):
        return 0

    # Carve the two leg openings: circles biting up into the lower sides,
    # leaving a narrow rounded crotch tab in the middle.
    lr = 0.42
    if (u - 0.10) ** 2 + (v - 0.94) ** 2 < lr * lr:
        return 0
    if (u - 0.90) ** 2 + (v - 0.94) ** 2 < lr * lr:
        return 0

    # Elastic waistband stripe near the top.
    if 0.30 <= v <= 0.355:
        return 2
    return 1


def draw(size):
    px = [(0, 0, 0, 0)] * (size * size)
    radius = size * 0.22          # rounded-corner radius

    def rounded_alpha(x, y):
        # distance into rounded-rect corners for anti-aliased edge
        dx = max(radius - x, x - (size - radius), 0)
        dy = max(radius - y, y - (size - radius), 0)
        d = math.hypot(dx, dy)
        return max(0.0, min(1.0, radius - d + 0.5))

    SS = 3                         # supersampling grid for smooth diaper edges
    offs = [(k + 0.5) / SS for k in range(SS)]

    for y in range(size):
        for x in range(size):
            i = y * size + x
            ra = rounded_alpha(x + 0.5, y + 0.5)
            if ra <= 0:
                continue

            cr = cg = cb = 0.0
            n_in = 0
            for sy in offs:
                v = (y + sy) / size
                for sx in offs:
                    u = (x + sx) / size
                    reg = diaper_region(u, v)
                    if reg == 0:
                        continue
                    n_in += 1
                    if reg == 2:
                        cr += ACCENT[0]; cg += ACCENT[1]; cb += ACCENT[2]
                    else:
                        cr += DROP[0]; cg += DROP[1]; cb += DROP[2]

            total = SS * SS
            frac = n_in / total
            if n_in:
                dr_, dg_, db_ = cr / n_in, cg / n_in, cb / n_in
            else:
                dr_ = dg_ = db_ = 0.0
            r = round(BG[0] * (1 - frac) + dr_ * frac)
            g = round(BG[1] * (1 - frac) + dg_ * frac)
            b = round(BG[2] * (1 - frac) + db_ * frac)

            px[i] = (r, g, b, int(255 * ra))
    return px


for size in (192, 512, 180):
    data = png(size, size, draw(size))
    name = "icons/apple-touch-icon.png" if size == 180 else f"icons/icon-{size}.png"
    with open(name, "wb") as f:
        f.write(data)
    print("wrote", name, len(data), "bytes")
