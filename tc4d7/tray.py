"""Tray for the Infineon KIT_A3G_TC4D7_LITE (AURIX TC4D7 lite kit), Bambu Lab A1, PLA.

The board has through-hole pins on its underside and shields on top (Arduino, mikroBUS, 2 x Shield2Go), so this is
an open tray, not a box: a floor with a low wall round it, the board held 12 mm up on four loose spacers (pins and
solder clear), nothing above the board so every header and connector stays reachable.

Board (user guide 002-41555 Rev. *A, Table 2): 131.0 x 66.0 mm. Its four mounting holes are not at the corners; their
centres were read off the guide's Figure 2 (+-0.5 mm), so the floor holes are Ø5.2 for an M3 / M2.5 bolt with
+-1 mm of play and a washer under the head. Measure the board and set HOLES if they turn out further off.

  bolt from below (head in the floor's counterbore) -> spacer -> board -> nut on top.
  4 x M3 x 20 (or M2.5 x 20 if the board holes are small) + nuts + washers.

Run:  uv run --with cadquery --with trimesh --with numpy python tc4d7/tray.py
"""
import os

import cadquery as cq
import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")

PCB = (131.0, 66.0, 1.6)
# hole centres from the board's top-left corner (top view, USB-C / DC jack on the right edge), mm
HOLES = [(60.5, 8.4), (111.8, 24.0), (59.5, 57.6), (111.9, 52.4)]
GAP = 1.5                   # board edge to wall
WALL = 2.4
FLOOR = 3.0
LIFT = 12.0                 # floor top to board underside
WALL_H = LIFT - 1.0         # the wall stops 1 mm under the board: connectors overhanging the edge are clear
BOLT_HOLE = 5.2             # play for the estimated hole positions
CBORE = (10.0, 2.0)         # head + washer pocket under the floor
SPACER = (7.0, 3.4)         # OD, ID
R_CORNER = 4.0

L, W = PCB[0] + 2 * (GAP + WALL), PCB[1] + 2 * (GAP + WALL)


def to_tray(x, y):
    """board top-left frame (y down) -> tray frame (centred, y up)."""
    return x - PCB[0] / 2, PCB[1] / 2 - y


def tray():
    t = cq.Workplane("XY").rect(L, W).extrude(FLOOR + WALL_H).edges("|Z").fillet(R_CORNER)
    t = t.cut(cq.Workplane("XY").workplane(offset=FLOOR).rect(L - 2 * WALL, W - 2 * WALL)
              .extrude(WALL_H + 1).edges("|Z").fillet(R_CORNER - WALL))
    pts = [to_tray(*h) for h in HOLES]
    t = t.cut(cq.Workplane("XY").pushPoints(pts).circle(BOLT_HOLE / 2).extrude(FLOOR + 1))
    t = t.cut(cq.Workplane("XY").pushPoints(pts).circle(CBORE[0] / 2).extrude(CBORE[1]))
    # vent slots in the floor under the board, clear of the bolt pads
    slots = []
    for x in np.arange(-50, 51, 12.5):
        if any(abs(x - px) < 9 for px, _ in pts):
            continue
        slots.append((x, 0))
    t = t.cut(cq.Workplane("XY").pushPoints(slots).slot2D(40, 5, 90).extrude(FLOOR + 1))
    t = t.faces("<Z").edges().chamfer(0.5)
    return t


def spacer():
    return cq.Workplane("XY").circle(SPACER[0] / 2).circle(SPACER[1] / 2).extrude(LIFT)


def mesh(wp, name):
    path = os.path.join(OUT, name + ".stl")
    cq.exporters.export(wp, path)
    m = trimesh.load(path)
    print(f"{name:7s} {m.extents.round(1)}  watertight={m.is_watertight}  bodies={len(m.split())}")
    return m


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    mesh(tray(), "tray")
    for i in range(4):
        mesh(spacer().translate((0, 0, 0)), f"spacer{i + 1}")
    # board clearance: every hole sits on the floor's bolt pad, and the PCB outline is inside the wall with GAP
    inner = (L - 2 * WALL, W - 2 * WALL)
    print(f"tray {L:.1f} x {W:.1f} x {FLOOR + WALL_H:.1f}; board {PCB[0]} x {PCB[1]} in {inner[0]:.1f} x {inner[1]:.1f}; "
          f"board underside {FLOOR + LIFT:.1f} above the bed side of the floor")
