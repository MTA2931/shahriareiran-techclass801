# Github: https://github.com/MTA2931/shahriareiran-techclass801

from machine import Pin, I2C
import framebuf
import time
import math
import random

# ==============================
# I2C Configuration
# ==============================

i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)

OLED_ADDR = 0x3C
TOUCH_ADDR = 0x38

# ==============================
# OLED Initialization
# ==============================

def cmd(c):
    i2c.writeto(OLED_ADDR, bytes([0x00, c]))


for c in (
    0xAE, 0x20, 0x00, 0x40, 0xA1, 0xA8, 63,
    0xC8, 0xD3, 0x00, 0xDA, 0x12, 0xD5, 0x80,
    0xD9, 0xF1, 0xDB, 0x30, 0x81, 0xFF,
    0xA4, 0xA6, 0x8D, 0x14, 0xAF
):
    cmd(c)


buf = bytearray(1 + 128 * 64 // 8)
buf[0] = 0x40

fb = framebuf.FrameBuffer(
    memoryview(buf)[1:],
    128,
    64,
    framebuf.MONO_VLSB
)


def show():
    cmd(0x21)
    cmd(0)
    cmd(127)

    cmd(0x22)
    cmd(0)
    cmd(7)

    i2c.writeto(OLED_ADDR, buf)


# ==============================
# Touch Detection
# ==============================

def is_touched():
    try:
        # FT6206 / FT6236 touch status register
        status = i2c.readfrom_mem(
            TOUCH_ADDR,
            0x02,
            1
        )[0]

        return (status & 0x0F) > 0

    except OSError:
        return False


# ==============================
# Face Configuration
# ==============================

EW, EH, R = 36, 40, 10

LX, RX, CY = 36, 92, 32

ox, oy = 0, 0

_inset_cache = {}


# ==============================
# Eye Drawing
# ==============================

def insets(r):
    if r not in _inset_cache:
        t = []

        for k in range(r):
            d = r - k
            t.append(
                r - int(math.sqrt(r * r - d * d))
            )

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

        fb.fill_rect(
            x0 + inset,
            y0 + i,
            w - 2 * inset,
            1,
            1
        )

    # Angry eyebrows
    if top or slant:
        for i in range(w):
            j = i if side == 0 else w - 1 - i

            c = top + (slant * j) // w

            if c > 0:
                fb.fill_rect(
                    x0 + i,
                    y0,
                    1,
                    min(c, h),
                    0
                )

    # Happy eyes
    if happy:
        for i in range(w):
            t = (2 * i - (w - 1)) / (w - 1)

            c = int(
                happy * (1 - t * t)
            ) + happy // 3

            if c > 0:
                fb.fill_rect(
                    x0 + i,
                    y0 + h - c,
                    1,
                    c,
                    0
                )


# ==============================
# Face Rendering
# ==============================

def frame(h=EH, top=0, slant=0, happy=0):
    fb.fill(0)

    eye(
        LX + ox,
        CY + oy,
        h,
        0,
        top,
        slant,
        happy
    )

    eye(
        RX + ox,
        CY + oy,
        h,
        1,
        top,
        slant,
        happy
    )

    show()


# ==============================
# Animations
# ==============================

def blink():
    for h in (EH, 26, 10, 2, 10, 26, EH):
        frame(h)
        time.sleep_ms(25)


def happy_face():
    frame(EH, happy=14)


def angry_face():
    frame(EH, top=2, slant=16)


def transition_to(happy):
    if happy:
        for s in range(4, -1, -1):
            frame(
                EH,
                top=2 * s // 4,
                slant=16 * s // 4,
                happy=14 * (4 - s) // 4
            )
            time.sleep_ms(25)

    else:
        for s in range(5):
            frame(
                EH,
                top=2 * s // 4,
                slant=16 * s // 4,
                happy=14 * (4 - s) // 4
            )
            time.sleep_ms(25)


# ==============================
# Main Program
# ==============================

current_mood = None
last_blink = time.ticks_ms()

happy_face()

while True:

    touched = is_touched()

    # --------------------------
    # Angry when touching
    # --------------------------

    if touched:

        if current_mood != "angry":
            transition_to(False)
            current_mood = "angry"

    # --------------------------
    # Happy when released
    # --------------------------

    else:

        if current_mood != "happy":
            transition_to(True)
            current_mood = "happy"

        # Random blinking while idle
        now = time.ticks_ms()

        if time.ticks_diff(now, last_blink) > random.randint(2500, 5000):
            blink()
            last_blink = time.ticks_ms()

    time.sleep_ms(35)
