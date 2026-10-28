"""Sleeve that slides over the original Xiaomi Mi Power Bank 10000 mAh (NDY-02-AN, 90 x 60.4 x 22 mm per the
e-catalog listing; Xiaomi's support page gives the same 207 g) and carries the CYD case on top.

A plain rectangular tube, open at both ends (ports, button and LEDs stay free, push the power bank out from
either end), printed standing on its end: every wall vertical, no bridges, no supports. On the wide face a
2.5 mm rim follows the CYD case's outline (90 x 54, R6 where it is full size, measured from ref/), so the
case sits in place; stick it in with double-sided foam tape. Put the CYD's port end and the power bank's
USB end the same way and join them with a short USB-A to USB-C cable.

Run:  uv run --with cadquery python sleeve.py
"""
import os

import cadquery as cq

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
os.makedirs(OUT, exist_ok=True)

BANK = (90.0, 60.4, 22.0)       # length, width, thickness (NDY-02-AN)
FIT = 0.3                       # per side
WALL = 2.0
CASE = (90.0, 54.0, 6.0)        # CYD case outline where it is full size, corner radius
CASE_FIT = 0.25
RIM = (1.6, 2.5)                # thickness, height
EDGE_R = 3.0

iw, it = BANK[1] + 2 * FIT, BANK[2] + 2 * FIT
ow, ot = iw + 2 * WALL, it + 2 * WALL
L = BANK[0]

# tube along z (print orientation): x = width, y = thickness, z = length; the CYD sits on the +y face
tube = (cq.Workplane("XY").rect(ow, ot).extrude(L).edges("|Z").fillet(EDGE_R)
        .cut(cq.Workplane("XY").rect(iw, it).extrude(L).edges("|Z").fillet(1.0)))
pw, pl, pr = CASE[1] + 2 * CASE_FIT, CASE[0] + 2 * CASE_FIT, CASE[2] + CASE_FIT
rim = (cq.Workplane("XZ", origin=(0, ot / 2, 0)).center(0, L / 2)
       .sketch().rect(pw + 2 * RIM[0], pl + 2 * RIM[0]).vertices().fillet(pr + RIM[0])
       .rect(pw, pl, mode="s").vertices().fillet(pr).finalize().extrude(-RIM[1]))
sleeve = tube.union(rim)
# trim the rim to the sleeve's length (it is 0.5 mm + rim longer than the 90 mm tube)
sleeve = sleeve.intersect(cq.Workplane("XY").rect(300, 300).extrude(L))
cq.exporters.export(sleeve, os.path.join(OUT, "sleeve.stl"))
bb = sleeve.val().BoundingBox()
print(f"sleeve {bb.xlen:.1f} x {bb.ylen:.1f} x {bb.zlen:.1f} (printed standing), inside {iw:.1f} x {it:.1f}, "
      f"valid={sleeve.val().isValid()}")
