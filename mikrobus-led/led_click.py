"""Printed "click" for a mikroBUS socket (AC164162 Curiosity Nano Base) that feeds a WS2812-type LED strip
(Seeed 104990014 Digital RGB LED Flexi-Strip, 60 LED/m, 5 V).

No PCB: a Click-S-sized plate (28.6 x 25.4, the mikroBUS outline) holds two ordinary 1x8 male pin headers in
press-fit slots 22.86 mm apart, plastic body in the plate, long pins down into the socket, short ends up.
A 1x3 male header at the far end takes the strip's lead (5 V / DIN / GND, in that order from the PWM side). Solder three
short insulated wires on top from the socket pins that matter -- PWM (data), +5V, GND, all on the PWM-side row --
to the 1x3. No printed text: the mikroBUS add-on corner notch (bottom right = GND end of the
PWM row) marks the orientation; match it to the outline on the socket's silkscreen.

Data: 3.3 V from the SAM E51 into a 5 V strip usually works over a short lead; add a 330 ohm resistor in the data
wire and a 470-1000 uF capacitor across 5 V/GND at the strip. 60 LEDs at full white draw ~3.6 A: the base's
5 V pin cannot supply that -- keep the brightness low or feed the strip's 5 V separately.

Run:  uv run --with cadquery python led_click.py   ->  led_click.stl
"""
import os

import cadquery as cq

HERE = os.path.dirname(os.path.abspath(__file__))
P = 2.54
L, W, T = 28.6, 27.4, 2.5          # Click S length; 2 mm wider than a Click (sockets are 29.2 apart) so each header slot keeps a 1 mm outer wall; T = header body height
ROW = 22.86 / 2                     # rows at y = +-11.43 (0.9" apart)
X0 = 3.0                            # first pin from the left (socket) end
FIT = 0.15                          # slot clearance over the header body (2.54 x 20.32 nominal); fit.py prints 8 steps
FIT_STEPS = [0.00, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35]
PWM_SIDE = 1                        # +y row carries PWM / INT / RX / TX / SCL / SDA / 5V / GND
PINS = {"PWM": 0, "5V": 6, "GND": 7}  # index along the row from pin 1
STRIP_X = L - 3.2                   # the strip's 1x3 header, across the plate (pins along y)
STRIP = {"5V": -P, "DI": 0.0, "G": P}


def pin_x(i):
    return X0 + P / 2 + i * P


def build(fit=FIT, mark=0):
    """mark: number of small pits on the top (1..8) to tell the fit-test pieces apart."""
    slot = (8 * P + fit + 0.1, P + fit)
    c = cq.Workplane("XY").box(L, W, T, centered=(False, True, False)).edges("|Z").fillet(1.0)
    c = c.faces("<Z").chamfer(0.3)
    for sy in (-1, 1):                                         # the two 1x8 headers
        c = c.cut(cq.Workplane("XY").center(X0 + slot[0] / 2, sy * ROW).rect(*slot).extrude(T + 1))
    c = c.cut(cq.Workplane("XY").center(STRIP_X, 0).rect(P + fit, 3 * P + fit + 0.1).extrude(T + 1))   # strip 1x3
    # no text (too small to print legibly). Orientation the mikroBUS way: the add-on standard keeps a notch at the
    # bottom-right corner -- seen from the top with AN / PWM (pin 1) at the top, PWM row on the right, that is the
    # GND end of the PWM row -- matching the outline printed on the host's socket silkscreen
    ch = 4.0
    corner = (L, PWM_SIDE * W / 2)
    c = c.cut(cq.Workplane("XY").polyline([corner, (L - ch, corner[1]), (L, corner[1] - PWM_SIDE * ch)]).close()
              .extrude(T + 1))
    if mark:                                                   # a row of pits between the rows, left end
        pts = [(X0 + 1.5 + 2.4 * k, -4.0) for k in range(mark)]
        c = c.cut(cq.Workplane("XY").workplane(offset=T - 0.8).pushPoints(pts).circle(0.7).extrude(1))
    return c


if __name__ == "__main__":
    import sys
    if "--fit" in sys.argv:                                    # fit test: 8 pieces, k pits = FIT_STEPS[k - 1]
        for k, f in enumerate(FIT_STEPS, 1):
            cq.exporters.export(build(f, k), os.path.join(HERE, "fit", f"fit_{k}.stl"))
            print(f"fit_{k}: {k} pits, clearance {f:.2f} mm")
        sys.exit()
    m = build()
    cq.exporters.export(m, os.path.join(HERE, "led_click.stl"))
    bb = m.val().BoundingBox()
    print("led_click", round(bb.xlen, 1), round(bb.ylen, 1), round(bb.zlen, 1), "valid", m.val().isValid())
