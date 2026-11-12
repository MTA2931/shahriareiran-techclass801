# Wokwi: https://wokwi.com/projects/480487526747000833
# Github: https://github.com/MTA2931/shahriareiran-techclass801

from machine import Pin, I2C
import framebuf
import time
import random
import math

i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
ADDR = 0x3C


def cmd(c):
    i2c.writeto(ADDR, bytes([0x00, c]))


for c in (0xAE, 0x20, 0x00, 0x40, 0xA1, 0xA8, 63, 0xC8, 0xD3, 0x00,
          0xDA, 0x12, 0xD5, 0x80, 0xD9, 0xF1, 0xDB, 0x30, 0x81, 0xFF,
          0xA4, 0xA6, 0x8D, 0x14, 0xAF):
    cmd(c)

buf = bytearray(1 + 128 * 64 // 8)
buf[0] = 0x40
fb = framebuf.FrameBuffer(memoryview(buf)[1:], 128, 64, framebuf.MONO_VLSB)


def show():
    cmd(0x21); cmd(0); cmd(127)
    cmd(0x22); cmd(0); cmd(7)
    i2c.writeto(ADDR, buf)


EW, EH, R = 36, 40, 10
LX, RX, CY = 36, 92, 32

ox, oy = 0, 0

_inset_cache = {}


def insets(r):
    if r not in _inset_cache:
        t = []
        for k in range(r):
            d = r - k
            t.append(r - int(math.sqrt(r * r - d * d)))
        _inset_cache[r] = t
    return _inset_cache[r]


def eye(cx, cy, h, side, top=0, slant=0, happy=0):
    w = EW
    r = min(R, h // 2)
    x0 = cx - w // 2
    y0 = cy - h // 2
    ins = insets(r) if r > 0 else []

    for i in range(h):
        k = min(i, h - 1 - i)
        inset = ins[k] if k < r else 0
        fb.fill_rect(x0 + inset, y0 + i, w - 2 * inset, 1, 1)

    if top or slant:
        for i in range(w):
            j = i if side == 0 else w - 1 - i
            c = top + (slant * j) // w
            if c > 0:
                fb.fill_rect(x0 + i, y0, 1, min(c, h), 0)

    if happy:
        for i in range(w):
            t = (2 * i - (w - 1)) / (w - 1)
            c = int(happy * (1 - t * t)) + happy // 3
            if c > 0:
                fb.fill_rect(x0 + i, y0 + h - c, 1, c, 0)


def frame(h=EH, top=0, slant=0, happy=0):
    fb.fill(0)
    eye(LX + ox, CY + oy, h, 0, top, slant, happy)
    eye(RX + ox, CY + oy, h, 1, top, slant, happy)
    show()


def blink():
    for h in (EH, 26, 10, 2, 10, 26, EH):
        frame(h)


def look_to(tx, ty, steps=4):
    global ox, oy
    sx, sy = ox, oy
    for i in range(1, steps + 1):
        ox = sx + (tx - sx) * i // steps
        oy = sy + (ty - sy) * i // steps
        frame()


def mood(top, slant, happy, hold=1000):
    for s in (1, 2, 3, 4):
        frame(EH, top * s // 4, slant * s // 4, happy * s // 4)
    time.sleep_ms(hold)
    for s in (3, 2, 1, 0):
        frame(EH, top * s // 4, slant * s // 4, happy * s // 4)


frame()

while True:
    a = random.randint(0, 11)
    if a < 3:
        blink()
    elif a == 3:
        blink()
        blink()
    elif a == 4:
        look_to(0, 0)
    elif a == 5:
        mood(top=0, slant=0, happy=14)
    elif a == 6:
        mood(top=2, slant=16, happy=0)
    else:
        look_to(random.randint(-14, 14), random.randint(-7, 7))
    time.sleep_ms(random.randint(300, 1200))
