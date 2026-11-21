#!/usr/bin/env python3
"""Valdorre passport spread — variant A (mountain microstate, slate-blue).

Procedurally draws an open passport spread for the invented alpine
Republic of Valdorre to /output/entry.png. Pure stdlib: zlib+struct PNG
encoder, tiny built-in 5x7 bitmap font, no network, no external assets.
Deterministic: two runs produce byte-identical output.
"""
import os
import struct
import zlib

W, H = 1024, 724

# ---------------------------------------------------------------- palette
PAPER = (223, 230, 234)      # pale blue-grey page
PAPER2 = (232, 234, 230)     # slightly warmer page tint
INK = (31, 46, 61)           # dark slate ink
SLATE = (46, 74, 98)         # header band
SLATE_DK = (36, 52, 74)      # coat / dark slate
SLATE_MD = (74, 102, 128)    # mid slate
LABEL = (96, 116, 134)       # field-label grey-blue
LINE = (150, 166, 178)       # hairlines
SKIN = (232, 185, 143)
SKIN_SH = (214, 164, 120)
HAIR = (58, 46, 38)
BEARD = (138, 125, 107)
SKY = (185, 203, 216)
RED = (126, 47, 47)          # Karnovia stamp ink
TEAL = (31, 92, 85)          # Suldara stamp ink
GREEN = (46, 90, 58)         # permit ink
GOLD = (198, 164, 92)
WHITE = (245, 245, 240)
BG = (24, 34, 46)            # spread surround

# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(bg) * (w * h)

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(c)

    def fill(self, x, y, w, h, c):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        row = bytes(c) * (x1 - x0)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            self.px[i:i + len(row)] = row

    def rect(self, x, y, w, h, c, t=1):
        self.fill(x, y, w, t, c)
        self.fill(x, y + h - t, w, t, c)
        self.fill(x, y, t, h, c)
        self.fill(x + w - t, y, t, h, c)

    def line(self, x0, y0, x1, y1, c, t=1):
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            self.fill(x0 - t // 2, y0 - t // 2, t, t, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, c, filled=False, t=1):
        if filled:
            for yy in range(-r, r + 1):
                dx = int((r * r - yy * yy) ** 0.5)
                self.fill(cx - dx, cy + yy, 2 * dx + 1, 1, c)
            return
        import math
        prev = None
        for deg in range(0, 361, 2):
            a = math.radians(deg)
            p = (int(cx + r * math.cos(a)), int(cy + r * math.sin(a)))
            if prev is not None:
                self.line(prev[0], prev[1], p[0], p[1], c, t)
            prev = p

    def ellipse(self, cx, cy, rx, ry, c, filled=False):
        import math
        if filled:
            for yy in range(-ry, ry + 1):
                dx = int(rx * (1 - (yy / ry) ** 2) ** 0.5)
                self.fill(cx - dx, cy + yy, 2 * dx + 1, 1, c)
            return
        prev = None
        for deg in range(0, 361, 3):
            a = math.radians(deg)
            p = (int(cx + rx * math.cos(a)), int(cy + ry * math.sin(a)))
            if prev is not None:
                self.line(prev[0], prev[1], p[0], p[1], c, 1)
            prev = p

    def poly(self, pts, c):
        """Fill a (convex) polygon by scanline."""
        ys = [p[1] for p in pts]
        for y in range(min(ys), max(ys) + 1):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    t = (y - y0) / (y1 - y0)
                    xs.append(x0 + t * (x1 - x0))
            if len(xs) >= 2:
                xs.sort()
                self.fill(int(xs[0]), y, int(xs[-1]) - int(xs[0]) + 1, 1, c)

# ---------------------------------------------------------------- 5x7 font
def _f(*rows):
    return rows

FONT = {
    'A': _f("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    'B': _f("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    'C': _f("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    'D': _f("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    'E': _f("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    'F': _f("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    'G': _f("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    'H': _f("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    'I': _f("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    'J': _f("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    'K': _f("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    'L': _f("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    'M': _f("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    'N': _f("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    'O': _f("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    'P': _f("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    'Q': _f("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    'R': _f("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    'S': _f("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    'T': _f("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    'U': _f("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    'V': _f("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    'W': _f("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
    'X': _f("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    'Y': _f("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    'Z': _f("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    '0': _f("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    '1': _f("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    '2': _f("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    '3': _f("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    '4': _f("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    '5': _f("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    '6': _f("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    '7': _f("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    '8': _f("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    '9': _f("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    ' ': _f("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    '.': _f("00000", "00000", "00000", "00000", "00000", "00110", "00110"),
    ',': _f("00000", "00000", "00000", "00000", "00100", "00100", "01000"),
    '-': _f("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    '/': _f("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    '<': _f("00010", "00100", "01000", "10000", "01000", "00100", "00010"),
    '>': _f("01000", "00100", "00010", "00001", "00010", "00100", "01000"),
    '(': _f("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ')': _f("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    ':': _f("00000", "00100", "00000", "00000", "00100", "00000", "00000"),
    ';': _f("00000", "00100", "00000", "00100", "00100", "01000", "00000"),
    "'": _f("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '"': _f("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
    '+': _f("00000", "00100", "00100", "01110", "00100", "00100", "00000"),
    '%': _f("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    '&': _f("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    '!': _f("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    '?': _f("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    '=': _f("00000", "00000", "01110", "00000", "01110", "00000", "00000"),
    '_': _f("00000", "00000", "00000", "00000", "00000", "00000", "11111"),
    '*': _f("00000", "00100", "10101", "01110", "10101", "00100", "00000"),
    '#': _f("01010", "01010", "11111", "01010", "11111", "01010", "01010"),
    '@': _f("01110", "10001", "10111", "10101", "10110", "10000", "01110"),
    '[': _f("01110", "01000", "01000", "01000", "01000", "01000", "01110"),
    ']': _f("01110", "00010", "00010", "00010", "00010", "00010", "01110"),
    '·': _f("00000", "00000", "00000", "01100", "01100", "00000", "00000"),
}
FALLBACK = FONT['?']


def text_w(s, scale):
    return len(s) * 6 * scale - scale


def draw_text(cv, x, y, s, scale, color, adv=6):
    s = s.upper()
    cx = x
    for ch in s:
        g = FONT.get(ch, FALLBACK)
        for r in range(7):
            row = g[r]
            for c in range(5):
                if row[c] == '1':
                    cv.fill(cx + c * scale, y + r * scale, scale, scale, color)
        cx += adv * scale
    return cx


def draw_text_c(cv, cx, y, s, scale, color, adv=6):
    draw_text(cv, cx - (len(s) * adv * scale - scale) // 2, y, s, scale, color, adv)


def wrap_lines(s, max_chars):
    words, lines, cur = s.split(' '), [], ''
    for w in words:
        t = (cur + ' ' + w).strip()
        if len(t) <= max_chars:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines

# ---------------------------------------------------------------- emblem
def emblem(cv, cx, cy, s):
    """Coat of arms: three mountain peaks under a sun, in a shield."""
    import math
    # shield outline
    cv.poly([(cx - 26 * s // 10, cy - 22 * s // 10), (cx + 26 * s // 10, cy - 22 * s // 10),
             (cx + 26 * s // 10, cy + 8 * s // 10), (cx, cy + 26 * s // 10),
             (cx - 26 * s // 10, cy + 8 * s // 10)], GOLD)
    cv.poly([(cx - 22 * s // 10, cy - 18 * s // 10), (cx + 22 * s // 10, cy - 18 * s // 10),
             (cx + 22 * s // 10, cy + 6 * s // 10), (cx, cy + 22 * s // 10),
             (cx - 22 * s // 10, cy + 6 * s // 10)], SLATE)
    # sun
    cv.circle(cx, cy - 8 * s // 10, 5 * s // 10, GOLD, filled=True)
    # peaks
    cv.poly([(cx - 20 * s // 10, cy + 18 * s // 10), (cx - 6 * s // 10, cy - 4 * s // 10),
             (cx + 2 * s // 10, cy + 18 * s // 10)], WHITE)
    cv.poly([(cx - 8 * s // 10, cy + 18 * s // 10), (cx + 8 * s // 10, cy - 8 * s // 10),
             (cx + 20 * s // 10, cy + 18 * s // 10)], (200, 214, 224))
    # snow caps
    cv.poly([(cx - 6 * s // 10, cy - 4 * s // 10), (cx - 9 * s // 10, cy + 1 * s // 10),
             (cx - 3 * s // 10, cy + 1 * s // 10)], GOLD)
    cv.poly([(cx + 8 * s // 10, cy - 8 * s // 10), (cx + 5 * s // 10, cy - 2 * s // 10),
             (cx + 11 * s // 10, cy - 2 * s // 10)], GOLD)


# ---------------------------------------------------------------- portrait
def portrait(cv, x, y, w, h):
    """Flat-illustration portrait: shepherd-official in a dark coat."""
    cv.fill(x, y, w, h, SKY)
    # distant peaks behind the sitter
    cv.poly([(x, y + 150), (x + 55, y + 92), (x + 110, y + 150)], (148, 168, 186))
    cv.poly([(x + 80, y + 150), (x + 140, y + 84), (x + 190, y + 150)], (168, 186, 200))
    cv.poly([(x + 140, y + 84), (x + 132, y + 98), (x + 148, y + 98)], WHITE)
    cv.poly([(x + 55, y + 92), (x + 47, y + 106), (x + 63, y + 106)], WHITE)
    # shoulders / dark coat
    cv.poly([(x + 18, y + h), (x + 42, y + 168), (x + 148, y + 168),
             (x + 172, y + h)], SLATE_DK)
    # coat lapels
    cv.poly([(x + 78, y + 172), (x + 95, y + 172), (x + 95, y + 236), (x + 84, y + 250)], SLATE_MD)
    cv.poly([(x + 112, y + 172), (x + 95, y + 172), (x + 95, y + 236), (x + 106, y + 250)], SLATE_MD)
    # white shirt + tie
    cv.poly([(x + 86, y + 168), (x + 104, y + 168), (x + 95, y + 196)], WHITE)
    cv.poly([(x + 92, y + 192), (x + 98, y + 192), (x + 100, y + 222), (x + 95, y + 232),
             (x + 90, y + 222)], (90, 60, 60))
    # brass buttons
    cv.circle(x + 70, y + 208, 3, GOLD, filled=True)
    cv.circle(x + 120, y + 208, 3, GOLD, filled=True)
    # edelweiss pin on lapel
    for dx, dy in [(0, -4), (4, 0), (0, 4), (-4, 0), (3, -3), (-3, -3), (3, 3), (-3, 3)]:
        cv.fill(x + 128 + dx - 1, y + 186 + dy - 1, 3, 3, WHITE)
    cv.circle(x + 128, y + 186, 2, GOLD, filled=True)
    # neck
    cv.fill(x + 82, y + 138, 26, 34, SKIN_SH)
    # head
    cv.ellipse(x + 95, y + 102, 42, 52, SKIN, filled=True)
    # ears
    cv.ellipse(x + 54, y + 104, 6, 10, SKIN, filled=True)
    cv.ellipse(x + 136, y + 104, 6, 10, SKIN, filled=True)
    # hair at sides (grey-flecked), narrow and tucked under the cap
    cv.poly([(x + 58, y + 98), (x + 62, y + 68), (x + 68, y + 98)], HAIR)
    cv.poly([(x + 132, y + 98), (x + 128, y + 68), (x + 122, y + 98)], HAIR)
    # flat cap
    cv.poly([(x + 50, y + 66), (x + 60, y + 44), (x + 130, y + 44), (x + 140, y + 66)], SLATE_DK)
    cv.fill(x + 48, y + 64, 94, 8, SLATE_DK)
    cv.fill(x + 52, y + 72, 86, 3, GOLD)
    # brows seated just above the eyes, eyes with whites so they read
    cv.fill(x + 69, y + 96, 14, 3, HAIR)
    cv.fill(x + 107, y + 96, 14, 3, HAIR)
    cv.ellipse(x + 76, y + 104, 9, 6, WHITE, filled=True)
    cv.ellipse(x + 114, y + 104, 9, 6, WHITE, filled=True)
    cv.circle(x + 76, y + 104, 3, INK, filled=True)
    cv.circle(x + 114, y + 104, 3, INK, filled=True)
    cv.line(x + 95, y + 106, x + 93, y + 122, SKIN_SH, 2)
    # grey shepherd's beard
    cv.poly([(x + 58, y + 122), (x + 132, y + 122), (x + 126, y + 158),
             (x + 95, y + 168), (x + 64, y + 158)], BEARD)
    # moustache over the mouth, mouth set mid-beard where it belongs
    cv.poly([(x + 74, y + 130), (x + 93, y + 130), (x + 93, y + 137),
             (x + 76, y + 137)], (120, 108, 92))
    cv.poly([(x + 97, y + 130), (x + 116, y + 130), (x + 114, y + 137),
             (x + 97, y + 137)], (120, 108, 92))
    cv.fill(x + 87, y + 144, 16, 2, (90, 82, 70))
    # photo frame
    cv.rect(x, y, w, h, INK, 2)
    cv.rect(x + 4, y + 4, w - 8, h - 8, LINE, 1)


# ---------------------------------------------------------------- stamps
def rect_stamp(cv, x, y, w, h, angle_deg, color, lines, scale=2):
    """Rotated rectangular border stamp, horizontal text inside."""
    import math
    a = math.radians(angle_deg)
    ca, sa = math.cos(a), math.sin(a)
    cx, cy = x + w // 2, y + h // 2

    def rot(px, py):
        dx, dy = px - cx, py - cy
        return (int(cx + dx * ca - dy * sa), int(cy + dx * sa + dy * ca))

    corners = [rot(x, y), rot(x + w, y), rot(x + w, y + h), rot(x, y + h)]
    for i in range(4):
        cv.line(corners[i][0], corners[i][1], corners[(i + 1) % 4][0],
                corners[(i + 1) % 4][1], color, 2)
    # inner border
    m = 7
    ic = [rot(x + m, y + m), rot(x + w - m, y + m),
          rot(x + w - m, y + h - m), rot(x + m, y + h - m)]
    for i in range(4):
        cv.line(ic[i][0], ic[i][1], ic[(i + 1) % 4][0], ic[(i + 1) % 4][1], color, 1)
    # text lines, centred, slight vertical stack
    total = len(lines) * (7 * scale + 6)
    ty = cy - total // 2
    for ln in lines:
        draw_text_c(cv, cx, ty, ln, scale, color)
        ty += 7 * scale + 6


def circle_stamp(cv, cx, cy, r, color, lines, scale=2):
    cv.circle(cx, cy, r, color, t=3)
    cv.circle(cx, cy, r - 7, color, t=1)
    total = sum((7 * sc + 5) for _, sc in lines) - 5
    ty = cy - total // 2
    for ln, sc in lines:
        draw_text_c(cv, cx, ty, ln, sc, color)
        ty += 7 * sc + 5


# ---------------------------------------------------------------- pages
def draw_left_page(cv, x, y, w, h):
    cv.fill(x, y, w, h, PAPER2)
    cv.rect(x, y, w, h, INK, 2)
    cv.rect(x + 8, y + 8, w - 16, h - 16, LINE, 1)
    draw_text(cv, x + 28, y + 26, "VISAS", 3, INK)
    draw_text(cv, x + 28, y + 52, "VISA - PAGE 4", 1, LABEL)
    draw_text(cv, x + w - 28 - text_w("VD4829137", 1), y + 52, "VD4829137", 1, LABEL)
    cv.line(x + 28, y + 72, x + w - 28, y + 72, LINE, 1)

    # Karnovia entry stamp
    rect_stamp(cv, x + 34, y + 92, 300, 104, -6, RED,
               ["KARNOVIA", "ENTRY", "02 SEP 2025", "DREVA BORDER POST"], 2)
    # Suldara entry stamp
    rect_stamp(cv, x + 120, y + 216, 300, 104, 5, TEAL,
               ["SULDARA", "ENTRY", "03 OCT 2025", "PASS OF MIRNA"], 2)
    # exit circular stamps (date line at scale 1 so it stays inside the ring)
    circle_stamp(cv, x + 108, y + 400, 58, RED,
                 [("KARNOVIA", 2), ("EXIT", 2), ("19 SEP 2025", 1)])
    circle_stamp(cv, x + 352, y + 400, 58, TEAL,
                 [("SULDARA", 2), ("EXIT", 2), ("21 OCT 2025", 1)])

    # --- mountain-pass permit: the telling paperwork detail
    bx, by, bw, bh = x + 28, y + 486, w - 56, 148
    cv.fill(bx, by, bw, bh, (222, 232, 222))
    cv.rect(bx, by, bw, bh, GREEN, 2)
    cv.rect(bx + 5, by + 5, bw - 10, bh - 10, GREEN, 1)
    draw_text_c(cv, bx + bw // 2, by + 12, "MOUNTAIN PASS PERMIT", 2, GREEN)
    cv.line(bx + 14, by + 34, bx + bw - 14, by + 34, GREEN, 1)
    draw_text(cv, bx + 14, by + 44, "VALID FOR PASSES ABOVE 2000 M", 1, GREEN)
    draw_text(cv, bx + 14, by + 62, "FOOT OR MULE ONLY - NO MOTORS", 1, GREEN)
    draw_text(cv, bx + 14, by + 80, "ABOVE TRELL PASS. ISSUED 01 SEP 2025", 1, GREEN)
    draw_text(cv, bx + 14, by + 98, "ALPINE AUTHORITY - TRELL", 1, GREEN)
    # small seal
    cv.circle(bx + bw - 34, by + 92, 22, GREEN, t=2)
    cv.circle(bx + bw - 34, by + 92, 16, GREEN, t=1)
    draw_text_c(cv, bx + bw - 34, by + 84, "VD", 1, GREEN)
    draw_text_c(cv, bx + bw - 34, by + 96, "2000M", 1, GREEN)
    draw_text_c(cv, x + w // 2, y + h - 34, "REPUBLIC OF VALDORRE - MINISTRY OF THE INTERIOR", 1, LABEL)


def field(cv, x, y, label, value, w=240):
    draw_text(cv, x, y, label, 1, LABEL)
    lines = wrap_lines(value, 19)
    ty = y + 10
    for ln in lines:
        draw_text(cv, x, ty, ln, 2, INK)
        ty += 16
    return ty


def draw_right_page(cv, x, y, w, h):
    cv.fill(x, y, w, h, PAPER)
    cv.rect(x, y, w, h, INK, 2)
    cv.rect(x + 8, y + 8, w - 16, h - 16, LINE, 1)
    # header band
    cv.fill(x + 2, y + 2, w - 4, 96, SLATE)
    emblem(cv, x + 52, y + 50, 10)
    draw_text(cv, x + 92, y + 16, "REPUBLIC OF", 1, (190, 204, 214))
    draw_text(cv, x + 92, y + 28, "VALDORRE", 4, WHITE)
    draw_text(cv, x + 92, y + 62, "PASSPORT  -  PASSEPORT", 1, (190, 204, 214))
    draw_text(cv, x + 92, y + 78, "ALPINE REPUBLIC - EST. 1848", 1, (190, 204, 214))
    draw_text(cv, x + w - 28 - text_w("VD4829137", 2), y + 28, "VD4829137", 2, GOLD)
    draw_text(cv, x + w - 28 - text_w("TYPE P", 1), y + 62, "TYPE P", 1, (190, 204, 214))

    # portrait
    portrait(cv, x + 28, y + 122, 190, 250)
    draw_text_c(cv, x + 123, y + 384, "PHOTOGRAPH OF HOLDER", 1, LABEL)

    # data fields
    fx = x + 240
    fy = y + 122
    for label, value in [
        ("SURNAME / NOM", "VELDAR"),
        ("GIVEN NAMES / PRENOMS", "TOMAS ALDRIC"),
        ("NATIONALITY / NATIONALITE", "VALDORRIAN"),
        ("DATE OF BIRTH", "12 JUN 1987"),
        ("PLACE OF BIRTH", "TRELL, VALDORRE"),
        ("SEX", "M"),
        ("DATE OF ISSUE", "14 MAR 2024"),
        ("DATE OF EXPIRY", "14 MAR 2034"),
        ("ISSUING AUTHORITY", "MINISTRY OF INTERIOR"),
    ]:
        fy = field(cv, fx, fy, label, value, 240) + 4

    # holder signature
    sy = y + 452
    draw_text(cv, x + 28, sy, "SIGNATURE OF HOLDER", 1, LABEL)
    cv.line(x + 28, sy + 26, x + 218, sy + 26, INK, 1)
    # signature squiggle
    import math
    prev = None
    for t in range(0, 181):
        px = x + 44 + t
        py = sy + 16 + int(6 * math.sin(math.radians(t * 3.2)))
        if prev is not None:
            cv.line(prev[0], prev[1], px, py, INK, 1)
        prev = (px, py)
    draw_text(cv, x + 240, sy, "OCCUPATION", 1, LABEL)
    draw_text(cv, x + 240, sy + 12, "SHEPHERD - ALPINE WARDEN", 1, INK)
    draw_text(cv, x + 240, sy + 28, "HEIGHT 182 CM - EYES GREY", 1, INK)

    # MRZ zone
    mz = y + 512
    cv.fill(x + 14, mz, w - 28, 128, (214, 220, 224))
    cv.rect(x + 14, mz, w - 28, 128, LINE, 1)
    draw_text(cv, x + 28, mz + 10, "MACHINE READABLE ZONE", 1, LABEL)
    draw_text(cv, x + 22, mz + 34,
              "P<VDOVELDAR<<TOMAS<ALDRIC<<<<<<<<<<<<<<<<<<<", 2, INK, adv=5)
    draw_text(cv, x + 22, mz + 66,
              "VD4829137<5VD0870612M3403143<<<<<<<<<<<<<<<4", 2, INK, adv=5)
    draw_text(cv, x + 28, mz + 102,
              "THIS PASSPORT IS THE PROPERTY OF THE", 1, LABEL)
    draw_text(cv, x + 28, mz + 114,
              "REPUBLIC OF VALDORRE.", 1, LABEL)


# ---------------------------------------------------------------- PNG encoder
def png_bytes(cv):
    raw = bytearray()
    stride = cv.w * 3
    for yy in range(cv.h):
        raw.append(0)
        raw += cv.px[yy * stride:(yy + 1) * stride]
    comp = zlib.compress(bytes(raw), 9)

    def chunk(typ, data):
        c = struct.pack(">I", len(data)) + typ + data
        return c + struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", comp) + chunk(b"IEND", b""))


def main():
    out_dir = "/output" if os.path.isdir("/output") else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "output")
    os.makedirs(out_dir, exist_ok=True)
    cv = Canvas(W, H, BG)
    # spread: two pages with a centre gutter shadow
    cv.fill(16, 16, 992, 692, (12, 18, 26))
    draw_left_page(cv, 24, 16, 488, 692)
    draw_right_page(cv, 512, 16, 488, 692)
    cv.fill(508, 16, 4, 692, (12, 18, 26))
    path = os.path.join(out_dir, "entry.png")
    with open(path, "wb") as fh:
        fh.write(png_bytes(cv))
    print("wrote", path, W, "x", H)


if __name__ == "__main__":
    main()
