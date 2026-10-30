"""Printed "click" for a mikroBUS socket (AC164162 Curiosity Nano Base) that feeds a WS2812-type LED strip
(Seeed 104990014 Digital RGB LED Flexi-Strip, 60 LED/m, 5 V).

No PCB: a Click-S-sized plate (28.6 x 25.4, the mikroBUS outline) holds two ordinary 1x8 male pin headers in
press-fit slots 22.86 mm apart, plastic body in the plate, long pins down into the socket, short ends up.
A 1x3 male header at the far end takes the strip's lead (5 V / DIN / GND). On top, three wire grooves run from
the socket pins that matter -- PWM (data), +5V, GND, all on the PWM-side row -- to the 1x3; solder short wires
in them. Labels are cut into the top. Check them against the silkscreen of the socket before soldering.

Data: 3.3 V from the SAM E51 into a 5 V strip usually works over a short lead; add a 330 ohm resistor in the data
wire and a 470-1000 uF capacitor across 5 V/GND at the strip. 60 LEDs at full white draw ~3.6 A: the base's
5 V pin cannot supply that -- keep the brightness low or feed the strip's 5 V separately.

Run:  uv run --with cadquery python led_click.py   ->  led_click.stl
"""
import os

import cadquery as cq

HERE = os.path.dirname(os.path.abspath(__file__))
P = 2.54
L, W, T = 28.6, 25.4, 2.5          # Click S outline; T = a pin header's plastic body height
ROW = 22.86 / 2                     # rows at y = +-11.43 (0.9" apart)
X0 = 3.0                            # first pin from the left (socket) end
SLOT = (8 * P + 0.25, P + 0.15)     # press-fit for the 2.5 x 20.3 header body
PWM_SIDE = 1                        # +y row carries PWM / INT / RX / TX / SCL / SDA / 5V / GND
PINS = {"PWM": 0, "5V": 6, "GND": 7}  # index along the row from pin 1
STRIP_X = L - 3.2                   # the strip's 1x3 header, across the plate (pins along y)
STRIP = {"5V": -P, "DI": 0.0, "G": P}
GROOVE = (1.4, 1.0)                 # wire groove width, depth


def pin_x(i):
    return X0 + P / 2 + i * P


def build():
    c = cq.Workplane("XY").box(L, W, T, centered=(False, True, False)).edges("|Z").fillet(1.0)
    c = c.faces("<Z").chamfer(0.3)
    for sy in (-1, 1):                                         # the two 1x8 headers
        c = c.cut(cq.Workplane("XY").center(X0 + SLOT[0] / 2, sy * ROW).rect(*SLOT).extrude(T + 1))
    c = c.cut(cq.Workplane("XY").center(STRIP_X, 0).rect(P + 0.15, 3 * P + 0.25).extrude(T + 1))   # strip 1x3
    # wire grooves on top: socket pin -> strip pin, an L along y then x
    y_row = PWM_SIDE * ROW
    for name, sx in (("PWM", "DI"), ("5V", "5V"), ("GND", "G")):
        x = pin_x(PINS[name])
        ys = STRIP[sx]
        y_mid = y_row - PWM_SIDE * 2.2 - PWM_SIDE * {"PWM": 0.0, "5V": 2.6, "GND": 5.2}[name]
        segs = [((x, y_row - PWM_SIDE * 1.4), (x, y_mid)), ((x, y_mid), (STRIP_X - 1.4, y_mid)),
                ((STRIP_X - 1.4, y_mid), (STRIP_X - 1.4, ys))]
        for (ax, ay), (bx, by) in segs:
            cx, cy = (ax + bx) / 2, (ay + by) / 2
            w = abs(bx - ax) + GROOVE[0]
            h = abs(by - ay) + GROOVE[0]
            c = c.cut(cq.Workplane("XY").workplane(offset=T - GROOVE[1]).center(cx, cy).rect(w, h).extrude(GROOVE[1] + 1))
    # labels
    def text(s, x, y, size=2.2):
        return cq.Workplane("XY").workplane(offset=T - 0.4).center(x, y).text(s, size, 1, halign="center", valign="center")
    c = c.cut(text("PWM", pin_x(0), y_row + PWM_SIDE * -0.1 - PWM_SIDE * 3.0 + 5.8 * 0, 1.6))
    c = c.cut(text("LED", L / 2 - 2, -ROW + 3.6, 3.0))
    for s, dy in STRIP.items():
        c = c.cut(text(s, STRIP_X + 0.1, dy, 1.4).translate((-2.9, 0, 0)))
    return c


if __name__ == "__main__":
    m = build()
    cq.exporters.export(m, os.path.join(HERE, "led_click.stl"))
    bb = m.val().BoundingBox()
    print("led_click", round(bb.xlen, 1), round(bb.ylen, 1), round(bb.zlen, 1), "valid", m.val().isValid())
