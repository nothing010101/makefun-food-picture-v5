#!/usr/bin/env python3
"""Gourmet cheeseburger — make.fun food-picture-01 entry (v5).

A tall, glossy cheeseburger drawn from scratch in pure Python (stdlib
only, deterministic, no network): golden brioche dome with sesame and a
gloss highlight, ruffled lettuce, pickles, red onion rings, tomato,
melted cheddar draped over a seared patty with drips, a toasted bottom
bun, a sauce drip, golden fries, and soft steam rising over a dark
wooden board. Warm directional light, dark moody background, burger
fills the frame so it reads clearly even at 300 px.

Writes /output/entry.png (or $MAKEFUN_OUTPUT_DIR/entry.png), 1024x1024.
"""
import math
import os
import random
import struct
import zlib

W = H = 1024
RNG = random.Random(20261115)


# ---------------------------------------------------------------- colors
def mix(c1, c2, t):
    return (int(c1[0] + (c2[0] - c1[0]) * t),
            int(c1[1] + (c2[1] - c1[1]) * t),
            int(c1[2] + (c2[2] - c1[2]) * t))


BG_TOP = (28, 18, 14)
BG_BOT = (66, 44, 26)
GLOW = (158, 92, 40)
WOOD_HI = (102, 66, 38)
WOOD_LO = (66, 42, 22)
WOOD_LINE = (48, 30, 16)
PARCH = (238, 228, 204)
PARCH_EDGE = (214, 200, 172)
BUN_HI = (252, 200, 112)
BUN_MID = (224, 152, 66)
BUN_LO = (182, 114, 46)
SESAME = (246, 224, 176)
SESAME_SH = (198, 158, 100)
LETTUCE_HI = (128, 196, 86)
LETTUCE_MID = (96, 166, 66)
LETTUCE_LO = (68, 138, 54)
PICKLE = (104, 150, 70)
PICKLE_DK = (70, 110, 48)
ONION = (166, 104, 150)
ONION_IN = (226, 206, 216)
TOMATO = (220, 60, 44)
TOMATO_IN = (240, 102, 76)
TOMATO_SEED = (252, 192, 162)
CHEESE_HI = (255, 178, 48)
CHEESE_LO = (244, 138, 24)
CHEESE_GLOSS = (255, 214, 116)
PATTY_HI = (128, 76, 40)
PATTY = (96, 54, 30)
PATTY_LO = (70, 38, 20)
CHAR = (46, 24, 12)
SAUCE = (238, 128, 62)
SAUCE_GLOSS = (255, 182, 122)
FRY_HI = (236, 186, 76)
FRY_LO = (212, 152, 54)
STEAM = (255, 248, 236)


# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h):
        self.w = w
        self.h = h
        self.buf = bytearray(w * h * 3)

    def hline(self, x0, x1, y, color):
        if y < 0 or y >= self.h:
            return
        x0 = max(0, int(x0))
        x1 = min(self.w - 1, int(x1))
        if x1 < x0:
            return
        n = x1 - x0 + 1
        i = (y * self.w + x0) * 3
        self.buf[i:i + 3 * n] = bytes(color) * n

    def blend_px(self, x, y, r, g, b, a):
        if x < 0 or x >= self.w or y < 0 or y >= self.h:
            return
        i = (y * self.w + x) * 3
        ia = 1.0 - a
        buf = self.buf
        buf[i] = int(buf[i] * ia + r * a)
        buf[i + 1] = int(buf[i + 1] * ia + g * a)
        buf[i + 2] = int(buf[i + 2] * ia + b * a)

    def disc(self, cx, cy, r, color):
        r = int(r)
        cx = int(cx)
        cy = int(cy)
        r2 = r * r
        for y in range(max(0, cy - r), min(self.h, cy + r + 1)):
            dy = y - cy
            d = r2 - dy * dy
            if d < 0:
                continue
            dx = int(d ** 0.5)
            self.hline(cx - dx, cx + dx, y, color)

    def ellipse(self, cx, cy, rx, ry, c_top, c_bot):
        cy = int(cy)
        cx = int(cx)
        for y in range(max(0, int(cy - ry)), min(self.h, int(cy + ry) + 1)):
            t = (y - (cy - ry)) / (2.0 * ry) if ry else 0.0
            t = 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)
            col = mix(c_top, c_bot, t)
            ny = (y - cy) / ry
            if abs(ny) >= 1.0:
                continue
            dx = int(rx * (1.0 - ny * ny) ** 0.5)
            self.hline(cx - dx, cx + dx, y, col)

    def vgrad_rect(self, x0, y0, x1, y1, c_top, c_bot):
        span = max(1, y1 - y0)
        for y in range(max(0, y0), min(self.h, y1 + 1)):
            t = (y - y0) / span
            self.hline(x0, x1, y, mix(c_top, c_bot, t))

    def blob(self, cx, cy, rx, ry, color, alpha):
        """Soft radial-falloff ellipse (steam, glow, shadow)."""
        x0 = max(0, int(cx - rx))
        x1 = min(self.w - 1, int(cx + rx))
        y0 = max(0, int(cy - ry))
        y1 = min(self.h - 1, int(cy + ry))
        r, g, b = color
        buf = self.buf
        w = self.w
        for y in range(y0, y1 + 1):
            ny = (y - cy) / ry
            ny2 = ny * ny
            row = y * w
            for x in range(x0, x1 + 1):
                nx = (x - cx) / rx
                d = nx * nx + ny2
                if d >= 1.0:
                    continue
                a = alpha * (1.0 - d) * (1.0 - d)
                if a < 0.012:
                    continue
                i = (row + x) * 3
                ia = 1.0 - a
                buf[i] = int(buf[i] * ia + r * a)
                buf[i + 1] = int(buf[i + 1] * ia + g * a)
                buf[i + 2] = int(buf[i + 2] * ia + b * a)

    def poly(self, pts, color):
        ys = [p[1] for p in pts]
        y0 = max(0, int(min(ys)))
        y1 = min(self.h - 1, int(max(ys)))
        n = len(pts)
        for y in range(y0, y1 + 1):
            xs = []
            for i in range(n):
                x0, yy0 = pts[i]
                x1, yy1 = pts[(i + 1) % n]
                if (yy0 <= y < yy1) or (yy1 <= y < yy0):
                    if yy1 != yy0:
                        xs.append(x0 + (y - yy0) * (x1 - x0) / (yy1 - yy0))
            if len(xs) >= 2:
                xs.sort()
                for k in range(0, len(xs) - 1, 2):
                    self.hline(int(xs[k]), int(xs[k + 1]), y, color)

    def capsule(self, x0, y0, x1, y1, r, color):
        dx = x1 - x0
        dy = y1 - y0
        dist = math.hypot(dx, dy)
        steps = max(1, int(dist / max(1.0, r * 0.5)))
        for i in range(steps + 1):
            t = i / steps
            self.disc(x0 + dx * t, y0 + dy * t, r, color)


# ---------------------------------------------------------------- png
def _chunk(tag, data):
    return (struct.pack(">I", len(data)) + tag + data
            + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))


def png_bytes(w, h, buf):
    raw = bytearray()
    rowlen = w * 3
    for y in range(h):
        raw.append(0)
        raw += buf[y * rowlen:(y + 1) * rowlen]
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", ihdr)
            + _chunk(b"IDAT", zlib.compress(bytes(raw), 6))
            + _chunk(b"IEND", b""))


# ---------------------------------------------------------------- scene
def paint_background(cv):
    cv.vgrad_rect(0, 0, W - 1, H - 1, BG_TOP, BG_BOT)
    # warm amber glow behind the burger, soft radial falloff
    cv.blob(512, 560, 520, 500, GLOW, 0.30)
    cv.blob(512, 560, 360, 350, mix(GLOW, (200, 130, 60), 0.4), 0.28)
    cv.blob(512, 560, 220, 210, mix(GLOW, (220, 150, 70), 0.5), 0.22)
    # darken the corners a little (vignette)
    for (x, y) in ((0, 0), (W, 0), (0, H), (W, H)):
        cv.blob(x, y, 420, 420, (10, 6, 5), 0.30)


def paint_board(cv):
    # round rustic wooden board
    cv.ellipse(512, 840, 472, 205, WOOD_HI, WOOD_LO)
    # plank lines and grain
    for (y, x0, x1) in ((760, 90, 934), (840, 60, 964), (920, 90, 934),
                         (990, 150, 874)):
        cv.hline(x0, x1, y, WOOD_LINE)
    for _ in range(26):
        x = RNG.randint(90, 934)
        y = RNG.randint(660, 1000)
        ln = RNG.randint(30, 110)
        cv.hline(x, x + ln, y, mix(WOOD_LO, WOOD_LINE, 0.5))
    # parchment sheet under the burger
    cv.ellipse(512, 890, 385, 132, PARCH, PARCH_EDGE)
    # soft shadow where the burger will sit
    cv.blob(512, 930, 305, 26, (30, 18, 10), 0.35)


def paint_fries(cv):
    # golden fries piled on the right, leaning on the burger
    sticks = [
        (800, 900, 880, 730, 15), (830, 905, 905, 745, 15),
        (860, 908, 930, 760, 14), (885, 905, 950, 775, 14),
        (775, 895, 845, 760, 13), (910, 900, 962, 800, 13),
        (845, 912, 900, 800, 13), (760, 880, 815, 790, 12),
    ]
    for (x0, y0, x1, y1, r) in sticks:
        col = mix(FRY_HI, FRY_LO, RNG.random() * 0.6)
        cv.capsule(x0, y0, x1, y1, r, col)
        # darker edge on the lower side
        cv.capsule(x0 + 4, y0 + 5, x1 + 4, y1 + 5, max(2, r - 9), FRY_LO)
    # salt specks
    for _ in range(46):
        x = RNG.randint(770, 960)
        y = RNG.randint(730, 905)
        cv.disc(x, y, RNG.randint(1, 2), (255, 250, 235))


def paint_top_bun(cv):
    # tall glossy brioche dome
    cv.ellipse(512, 500, 272, 212, BUN_HI, BUN_LO)
    # warm light from the upper left: soft gloss
    cv.blob(400, 370, 140, 62, (255, 236, 190), 0.30)
    cv.blob(375, 340, 85, 32, (255, 246, 220), 0.30)
    # sesame seeds scattered on the dome
    for _ in range(46):
        for _try in range(12):
            x = RNG.randint(280, 744)
            y = RNG.randint(320, 590)
            nx = (x - 512) / 272.0
            ny = (y - 500) / 212.0
            if nx * nx + ny * ny < 0.72:
                break
        else:
            continue
        cv.disc(x, y + 2, 6, SESAME_SH)
        cv.ellipse(x, y, 11, 6, SESAME, mix(SESAME, (220, 180, 120), 0.45))


def _leaf_band(top_y, amp, tip, color):
    """Wavy band with pointed leaf tips along its bottom edge."""
    pts = []
    x = 192
    while x <= 832:
        pts.append((x, top_y + int(amp * math.sin(x / 48.0))))
        x += 20
    x = 832
    while x >= 192:
        # pointed tips: alternate deep and shallow bottom points
        deep = (x // 40) % 2 == 0
        pts.append((x, top_y + tip + (24 if deep else -6)
                    + int(amp * math.sin(x / 43.0 + 1.2))))
        x -= 20
    return pts


def paint_lettuce(cv):
    # full ruffled leaves sticking out past the bun on both sides
    cv.poly(_leaf_band(606, 16, 56, LETTUCE_LO), LETTUCE_LO)
    cv.poly(_leaf_band(622, 20, 50, LETTUCE_HI), LETTUCE_HI)
    # curled leaf tips hanging below the band
    for (x, y, r) in ((240, 682, 22), (330, 690, 24), (430, 688, 22),
                      (540, 692, 24), (650, 688, 22), (760, 680, 21)):
        cv.disc(x, y, r, LETTUCE_MID)


def paint_pickles_onion(cv):
    # dill pickle slices
    for (x, y) in ((352, 656), (512, 660), (668, 656)):
        cv.disc(x, y, 23, PICKLE)
        for _ in range(6):
            a = RNG.random() * 6.283
            d = RNG.randint(4, 14)
            cv.disc(x + int(d * math.cos(a)), y + int(d * math.sin(a)), 3, PICKLE_DK)
        cv.disc(x - 5, y - 6, 5, mix(PICKLE, (180, 210, 130), 0.5))
    # red onion rings
    for (x, y) in ((430, 648), (592, 648)):
        cv.disc(x, y, 27, ONION)
        cv.disc(x, y, 19, ONION_IN)
        cv.disc(x, y, 11, ONION)


def paint_tomato(cv):
    cv.ellipse(512, 705, 285, 42, TOMATO, mix(TOMATO, (170, 36, 28), 0.7))
    cv.ellipse(512, 703, 252, 28, TOMATO_IN, mix(TOMATO_IN, (214, 70, 52), 0.6))
    for (x, y) in ((380, 700), (470, 712), (560, 700), (650, 710)):
        cv.ellipse(x, y, 12, 6, TOMATO_SEED, mix(TOMATO_SEED, (240, 150, 120), 0.5))
    cv.blob(400, 688, 120, 16, (255, 150, 120), 0.25)


def paint_patty(cv):
    # thick seared beef patty
    cv.ellipse(512, 790, 315, 58, PATTY_HI, PATTY_LO)
    # seared highlight along the top edge
    for a in range(200, 341, 4):
        t = math.radians(a)
        x = 512 + 300 * math.cos(t)
        y = 790 + 48 * math.sin(t)
        cv.disc(x, y, 6, mix(PATTY_HI, (170, 105, 60), 0.55))
    # char speckles and meat grain
    for _ in range(150):
        for _try in range(10):
            x = RNG.randint(220, 804)
            y = RNG.randint(742, 838)
            nx = (x - 512) / 315.0
            ny = (y - 790) / 58.0
            if nx * nx + ny * ny < 0.92:
                break
        else:
            continue
        col = CHAR if RNG.random() < 0.45 else mix(PATTY, (150, 95, 55), RNG.random())
        cv.disc(x, y, RNG.randint(2, 4), col)


def paint_cheese(cv):
    # cheddar slice draped over the patty, wavy bottom edge
    pts = [(222, 736)]
    x = 222
    while x <= 802:
        pts.append((x, 748 + int(14 * math.sin(x / 47.0))))
        x += 24
    pts.append((802, 736))
    pts.append((802, 724))
    pts.append((222, 724))
    cv.poly(pts, CHEESE_HI)
    # glossy top edge
    cv.hline(240, 784, 728, CHEESE_GLOSS)
    # molten drips hanging over the patty: wide, with a rounded bulb
    for (x, y0, y1, r) in ((398, 748, 798, 17), (512, 752, 812, 19),
                           (626, 748, 790, 16)):
        cv.capsule(x, y0, x + 3, y1, r, CHEESE_LO)
        cv.disc(x + 3, y1, r + 4, CHEESE_LO)
        cv.capsule(x - 5, y0, x - 2, y1 - 14, max(2, r - 10), CHEESE_GLOSS)


def paint_bottom_bun(cv):
    cv.ellipse(512, 875, 295, 62, BUN_MID, mix(BUN_LO, (150, 92, 36), 0.7))
    # light top edge where it meets the patty
    cv.ellipse(512, 838, 280, 18, mix(BUN_HI, BUN_MID, 0.5), BUN_MID)
    # toasted bottom rim
    for a in range(20, 161, 5):
        t = math.radians(a)
        x = 512 + 282 * math.cos(t)
        y = 875 + 52 * math.sin(t)
        cv.disc(x, y, 6, mix(BUN_LO, (140, 82, 30), 0.6))


def paint_sauce(cv):
    # glossy sauce smear on the parchment, and a short drip off the cheese
    cv.ellipse(820, 930, 42, 12, SAUCE, mix(SAUCE, (190, 90, 40), 0.6))
    cv.capsule(700, 752, 706, 800, 9, SAUCE)
    cv.disc(706, 802, 12, SAUCE)
    cv.disc(703, 798, 5, SAUCE_GLOSS)


def paint_steam(cv):
    # soft steam columns rising off the hot burger
    for (bx, base_y, top_y, amp) in ((410, 290, 50, 18), (480, 275, 30, 22),
                                     (555, 275, 40, 20), (620, 290, 60, 16)):
        y = base_y
        while y > top_y:
            t = (base_y - y) / (base_y - top_y)
            x = bx + int(amp * math.sin(y / 46.0 + bx))
            r = 26 + int(18 * t)
            cv.blob(x, y, r, 34, STEAM, 0.16 + 0.08 * t)
            y -= 24


def paint_garnish(cv):
    # scattered sesame and flaky salt on the board
    for _ in range(12):
        x = RNG.randint(140, 900)
        y = RNG.randint(940, 1010)
        cv.ellipse(x, y, 9, 5, SESAME, SESAME_SH)
    for _ in range(24):
        x = RNG.randint(120, 920)
        y = RNG.randint(700, 1010)
        cv.disc(x, y, 1, (255, 250, 235))
    # one crisp lettuce leaf on the left of the board
    cv.ellipse(180, 900, 70, 26, LETTUCE_HI, LETTUCE_MID)
    cv.ellipse(180, 896, 48, 16, LETTUCE_MID, LETTUCE_LO)


def build():
    cv = Canvas(W, H)
    paint_background(cv)
    paint_board(cv)
    paint_fries(cv)
    paint_top_bun(cv)
    paint_lettuce(cv)
    paint_pickles_onion(cv)
    paint_tomato(cv)
    paint_patty(cv)
    paint_cheese(cv)
    paint_bottom_bun(cv)
    paint_sauce(cv)
    paint_garnish(cv)
    paint_steam(cv)
    return cv


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "out"
    os.makedirs(outdir, exist_ok=True)
    cv = build()
    data = png_bytes(W, H, cv.buf)
    path = os.path.join(outdir, "entry.png")
    with open(path, "wb") as fh:
        fh.write(data)
    print("wrote %s (%d bytes)" % (path, len(data)))


if __name__ == "__main__":
    main()
