#!/usr/bin/env python3
"""news-image-01 rev-3: one front page summing up Friday 13 November 2026.

Five stories, one page: the FAA nationwide ground stop (lead), Ukraine's
~1,200-drone attack on Russia, Nvidia CEO Jensen Huang resigning, the
Microsoft 365 outage entering its second day, and the Qatar-Turkey mutual
defense pact. All facts as reported on 13 Nov 2026 (AP / Reuters / USA TODAY).

Drawn procedurally with stdlib only: own PNG encoder, own 5x7 bitmap font,
no network, no randomness, no time — two runs write identical bytes.
"""

import os
import struct
import zlib

W = 1024
H = 1024

# ---------------------------------------------------------------- font (5x7)
# Each glyph: 7 rows of 5 bits, '#' = on.
FONT = {
    'A': ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    'B': ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    'C': ("01111", "10000", "10000", "10000", "10000", "10000", "01111"),
    'D': ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    'E': ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    'F': ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    'G': ("01111", "10000", "10000", "10111", "10001", "10001", "01110"),
    'H': ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    'I': ("11111", "00100", "00100", "00100", "00100", "00100", "11111"),
    'J': ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    'K': ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    'L': ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    'M': ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    'N': ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    'O': ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    'P': ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    'Q': ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    'R': ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    'S': ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    'T': ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    'U': ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    'V': ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    'W': ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    'X': ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    'Y': ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    'Z': ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    '0': ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    '1': ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    '2': ("01110", "10001", "00001", "00010", "00100", "01000", "11111"),
    '3': ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    '4': ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    '5': ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    '6': ("01110", "10000", "10000", "11110", "10001", "10001", "01110"),
    '7': ("11111", "00001", "00010", "00100", "00100", "00100", "00100"),
    '8': ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    '9': ("01110", "10001", "10001", "01111", "00001", "00001", "01110"),
    ' ': ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    '.': ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ',': ("00000", "00000", "00000", "00000", "00000", "01100", "01000"),
    ':': ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    '-': ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    '+': ("00000", "00100", "00100", "01110", "00100", "00100", "00000"),
    '/': ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    '(': ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ')': ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    '&': ("01100", "10010", "10010", "01000", "10101", "10010", "01101"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '!': ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    '?': ("01110", "10001", "00001", "00010", "00100", "00000", "00100"),
    '%': ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
}


def text_width(s, scale):
    return len(s) * 6 * scale - scale


# ---------------------------------------------------------------- framebuffer
class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(bg * (w * h))

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(c)

    def rect(self, x, y, w, h, c):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        row = bytes(c) * (x1 - x0)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            self.px[i:i + (x1 - x0) * 3] = row

    def line(self, x0, y0, x1, y1, c, t=1):
        dx = x1 - x0
        dy = y1 - y0
        steps = max(abs(dx), abs(dy), 1)
        r = t // 2
        for s in range(steps + 1):
            x = x0 + dx * s // steps
            y = y0 + dy * s // steps
            self.rect(x - r, y - r, t, t, c)

    def circle(self, cx, cy, r, c):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r:
                    self.set(xx, yy, c)

    def ring(self, cx, cy, r, c, t=3):
        for yy in range(cy - r - t, cy + r + t + 1):
            for xx in range(cx - r - t, cx + r + t + 1):
                d = (xx - cx) ** 2 + (yy - cy) ** 2
                if (r - t) ** 2 <= d <= (r + t) ** 2:
                    self.set(xx, yy, c)

    def tri(self, x0, y0, x1, y1, x2, y2, c):
        # Filled triangle via barycentric test over its bounding box.
        minx = max(0, min(x0, x1, x2))
        maxx = min(self.w - 1, max(x0, x1, x2))
        miny = max(0, min(y0, y1, y2))
        maxy = min(self.h - 1, max(y0, y1, y2))
        d = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
        if d == 0:
            return
        for yy in range(miny, maxy + 1):
            for xx in range(minx, maxx + 1):
                a = ((y1 - y2) * (xx - x2) + (x2 - x1) * (yy - y2)) / d
                b = ((y2 - y0) * (xx - x2) + (x0 - x2) * (yy - y2)) / d
                cc = 1.0 - a - b
                if a >= 0 and b >= 0 and cc >= 0:
                    self.set(xx, yy, c)

    def text(self, x, y, s, scale, c, align="left"):
        w = text_width(s, scale)
        if align == "center":
            x -= w // 2
        elif align == "right":
            x -= w
        for ci, ch in enumerate(s):
            g = FONT.get(ch.upper())
            if g is None:
                continue
            ox = x + ci * 6 * scale
            for r, row in enumerate(g):
                for col, bit in enumerate(row):
                    if bit == '1':
                        self.rect(ox + col * scale, y + r * scale,
                                  scale, scale, c)

    def vgrad(self, x, y, w, h, top, bot):
        for yy in range(h):
            f = yy / max(1, h - 1)
            c = tuple(int(top[i] + (bot[i] - top[i]) * f) for i in range(3))
            self.rect(x, y + yy, w, 1, c)


# ---------------------------------------------------------------- PNG encoder
def _chunk(typ, data):
    return (struct.pack(">I", len(data)) + typ + data +
            struct.pack(">I", zlib.crc32(typ + data) & 0xffffffff))


def write_png(path, cv):
    raw = bytearray()
    for y in range(cv.h):
        raw.append(0)
        raw += cv.px[y * cv.w * 3:(y + 1) * cv.w * 3]
    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    data = (b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", ihdr) +
            _chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + _chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(data)
    return len(data)


# ---------------------------------------------------------------- palette
CREAM = (246, 241, 229)
NAVY = (16, 36, 62)
RED = (192, 57, 43)
INK = (20, 20, 20)
GREY = (90, 90, 90)
WHITE = (255, 255, 255)
SKY_TOP = (176, 208, 232)
SKY_BOT = (238, 242, 246)
TARMAC = (52, 52, 52)
PLANE = (28, 44, 68)
YELLOW = (255, 200, 40)
ORANGE = (230, 126, 34)


# ---------------------------------------------------------------- icons
def draw_plane(cv, x, y, s, c):
    """Side-view airliner silhouette, nose right, origin at tail bottom."""
    # fuselage
    cv.rect(x, y - 14 * s, 46 * s, 10 * s, c)
    cv.circle(x + 46 * s, y - 9 * s, 5 * s, c)
    cv.rect(x + 40 * s, y - 14 * s, 8 * s, 10 * s, c)
    # tail fin
    cv.tri(x + 2 * s, y - 14 * s, x + 2 * s, y - 30 * s,
           x + 12 * s, y - 14 * s, c)
    # wing (swept, below fuselage)
    cv.tri(x + 18 * s, y - 4 * s, x + 30 * s, y - 4 * s,
           x + 24 * s, y + 8 * s, c)
    # tailplane
    cv.tri(x + 4 * s, y - 6 * s, x + 12 * s, y - 6 * s,
           x + 8 * s, y + 2 * s, c)
    # engines
    cv.rect(x + 20 * s, y + 2 * s, 8 * s, 4 * s, c)
    cv.rect(x + 32 * s, y + 2 * s, 8 * s, 4 * s, c)
    # windows (cut in sky colour)
    for wx in range(x + 12 * s, x + 42 * s, 4 * s):
        cv.rect(wx, y - 12 * s, 2 * s, 3 * s, SKY_BOT)


def draw_tower(cv, x, y, s, c):
    """Control tower: shaft + cab, base at (x, y)."""
    cv.rect(x, y - 58 * s, 8 * s, 58 * s, c)
    cv.rect(x - 6 * s, y - 72 * s, 20 * s, 14 * s, c)
    cv.rect(x - 3 * s, y - 70 * s, 14 * s, 6 * s, SKY_BOT)
    cv.rect(x - 8 * s, y - 58 * s, 24 * s, 3 * s, c)


def draw_drone(cv, cx, cy, s, c):
    """Quadcopter seen from the side-front: body, 4 arms, 4 rotors."""
    cv.rect(cx - 10 * s, cy - 4 * s, 20 * s, 9 * s, c)
    cv.rect(cx - 3 * s, cy + 5 * s, 6 * s, 6 * s, c)
    for sx in (-1, 1):
        cv.line(cx - 8 * s, cy, cx - 26 * s, cy - 8 * s, c, 2 * s)
        cv.line(cx + 8 * s, cy, cx + 26 * s, cy - 8 * s, c, 2 * s)
        cv.line(cx - 26 * s, cy - 8 * s, cx - 26 * s, cy - 2 * s, c, 2 * s)
        cv.line(cx + 26 * s, cy - 8 * s, cx + 26 * s, cy - 2 * s, c, 2 * s)
        cv.line(cx - 36 * s, cy - 12 * s, cx - 16 * s, cy - 12 * s, c, 2 * s)
        cv.line(cx + 16 * s, cy - 12 * s, cx + 36 * s, cy - 12 * s, c, 2 * s)
    cv.circle(cx, cy, 3 * s, YELLOW)


def draw_burst(cv, cx, cy, r, c1, c2):
    """Explosion starburst: alternating long/short spikes."""
    for k in range(12):
        ang = k * 30
        rad = r if k % 2 == 0 else r // 2
        import math
        x1 = cx + int(rad * math.cos(math.radians(ang)))
        y1 = cy + int(rad * math.sin(math.radians(ang)))
        cv.tri(cx, cy, x1, y1,
               cx + int(rad * 0.45 * math.cos(math.radians(ang + 15))),
               cy + int(rad * 0.45 * math.sin(math.radians(ang + 15))),
               c1 if k % 2 == 0 else c2)
    cv.circle(cx, cy, r // 3, c2)


def draw_chip(cv, cx, cy, s, c, label="AI"):
    """Microchip: body, pins, inner die with a label."""
    cv.rect(cx - 34 * s, cy - 34 * s, 68 * s, 68 * s, c)
    cv.rect(cx - 20 * s, cy - 20 * s, 40 * s, 40 * s, (16, 36, 62))
    for i in range(5):
        off = -28 * s + i * 14 * s
        cv.rect(cx + off, cy - 44 * s, 5 * s, 10 * s, c)
        cv.rect(cx + off, cy + 34 * s, 5 * s, 10 * s, c)
        cv.rect(cx - 44 * s, cy + off, 10 * s, 5 * s, c)
        cv.rect(cx + 34 * s, cy + off, 10 * s, 5 * s, c)
    cv.text(cx, cy - 10 * s, label, 3 * s, YELLOW, align="center")


def draw_cloud_x(cv, cx, cy, s, c):
    """Cloud with a red X over it (service down)."""
    cv.circle(cx - 22 * s, cy + 6 * s, 16 * s, c)
    cv.circle(cx, cy - 4 * s, 20 * s, c)
    cv.circle(cx + 22 * s, cy + 6 * s, 16 * s, c)
    cv.rect(cx - 38 * s, cy, 76 * s, 16 * s, c)
    cv.line(cx - 30 * s, cy - 30 * s, cx + 30 * s, cy + 30 * s, RED, 7 * s)
    cv.line(cx + 30 * s, cy - 30 * s, cx - 30 * s, cy + 30 * s, RED, 7 * s)


def draw_flags(cv, x, y, s):
    """Two flags on poles: Qatar (maroon, white serrated band) + Turkey
    (red, white crescent)."""
    # poles
    cv.rect(x, y - 62 * s, 3 * s, 62 * s, INK)
    cv.rect(x + 52 * s, y - 62 * s, 3 * s, 62 * s, INK)
    # Qatar flag (left): maroon field, white serrated hoist band
    cv.rect(x + 3 * s, y - 62 * s, 46 * s, 30 * s, (139, 35, 56))
    for k in range(4):
        yy = y - 62 * s + k * 8 * s
        cv.tri(x + 3 * s, yy, x + 3 * s, yy + 8 * s, x + 13 * s, yy + 4 * s,
               WHITE)
    # Turkey flag (right): red field, white crescent
    cv.rect(x + 55 * s, y - 62 * s, 46 * s, 30 * s, (227, 10, 23))
    cv.circle(x + 74 * s, y - 47 * s, 9 * s, WHITE)
    cv.circle(x + 77 * s, y - 47 * s, 8 * s, (227, 10, 23))
    cv.circle(x + 88 * s, y - 47 * s, 2 * s, WHITE)


# ---------------------------------------------------------------- composition
def panel(cv, x, y, w, h, bg, topic, headline, subhead, icon):
    cv.rect(x, y, w, h, bg)
    cv.rect(x, y, w, 36, tuple(max(0, v - 18) for v in bg))
    cv.text(x + 16, y + 11, topic, 2, WHITE)
    icon()
    cv.text(x + w // 2, y + 150, headline, 4, WHITE, align="center")
    cv.text(x + w // 2, y + 186, subhead, 2, (220, 220, 220), align="center")


def build():
    cv = Canvas(W, H, CREAM)
    # masthead
    cv.rect(0, 0, W, 100, NAVY)
    cv.text(W // 2, 16, "THE WORLD", 7, WHITE, align="center")
    cv.text(W // 2, 72, "FRIDAY, NOVEMBER 13, 2026", 2, (200, 210, 225),
            align="center")
    cv.rect(0, 100, W, 6, RED)
    # lead: sky, runway, grounded planes
    cv.vgrad(0, 106, W, 294, SKY_TOP, SKY_BOT)
    draw_tower(cv, 880, 400, 2, PLANE)
    draw_plane(cv, 760, 172, 1, PLANE)
    cv.ring(783, 161, 48, RED, 5)
    cv.line(746, 124, 820, 198, RED, 5)
    cv.rect(0, 400, W, 40, TARMAC)
    for dx in range(20, W, 80):
        cv.rect(dx, 418, 40, 4, WHITE)
    draw_plane(cv, 80, 400, 3, PLANE)
    draw_plane(cv, 560, 400, 2, PLANE)
    # lead headline + facts
    cv.text(W // 2, 458, "U.S. FLIGHTS GROUNDED", 6, RED, align="center")
    cv.text(W // 2, 512, "FAA HALTS ALL DEPARTURES AFTER TELECOM FAILURE",
            2, INK, align="center")
    cv.text(W // 2, 534, "4+ HOURS - 1,000+ CANCELLED - 10,000 DELAYED",
            2, GREY, align="center")
    cv.rect(0, 556, W, 4, NAVY)
    # four stories, 2 x 2
    panel(cv, 0, 564, 508, 226, (31, 58, 95), "UKRAINE", "1,200 DRONES",
          "ONE OF THE WAR'S BIGGEST",
          lambda: (draw_drone(cv, 220, 674, 2, (200, 210, 225)),
                   draw_burst(cv, 380, 660, 26, YELLOW, ORANGE)))
    panel(cv, 516, 564, 508, 226, (20, 83, 45), "NVIDIA", "CEO RESIGNS",
          "HUANG OUT AMID SPY CLAIMS",
          lambda: draw_chip(cv, 770, 674, 1, (118, 185, 0)))
    panel(cv, 0, 798, 508, 226, (27, 42, 74), "MICROSOFT 365",
          "OUTAGE DAY 2", "OUTLOOK, TEAMS STILL DOWN",
          lambda: draw_cloud_x(cv, 254, 898, 1, (200, 210, 225)))
    panel(cv, 516, 798, 508, 226, (91, 31, 42), "QATAR - TURKEY",
          "DEFENSE PACT", "MUTUAL DEFENSE DEAL SIGNED",
          lambda: draw_flags(cv, 716, 928, 1))
    return cv


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    cv = build()
    n = write_png(os.path.join(out_dir, "entry.png"), cv)
    print("wrote entry.png", n, "bytes")


if __name__ == "__main__":
    main()

