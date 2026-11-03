"""One-piece tray for the Infineon KIT_A3G_TC4D7_LITE (AURIX TC4D7 lite kit), Bambu Lab A1, PLA.

The board has through-hole pins on its underside and shields on top (Arduino, mikroBUS, 2 x Shield2Go), so this is
an open tray, not a box: a floor, a low wall round it and four posts that hold the board 12 mm up (pins and solder
clear). Posts, wall and floor are one print; nothing above the board, so every header and connector stays reachable.

Board (user guide 002-41555 Rev. *A, Table 2): 131.0 x 66.0 mm. Its four mounting holes are not at the corners; their
centres were read off the guide's Figure 2 (+-0.5 mm). The posts can't move, so the play is in the bolt instead: each
post has a Ø4.2 bore for an M3 bolt (+-0.6 mm) and the head sits in a Ø8 counterbore under the floor. Measure the
board and set HOLES if it turns out further off.

  M3 bolt from below (head hidden in the floor) -> post -> board -> nut on top.
  4 x M3 x 20 + nuts (+ washers under the nuts).

Design: soft R6 corners, a full round on the wall top, filleted post roots, a 0.6 mm chamfer on the bed edge (no
elephant foot) and a row of equal rounded slots under the board for air. Prints flat, no supports, no brim.

Run:  uv run --with cadquery --with trimesh --with numpy --with vtk --with matplotlib --with scipy --with networkx \\
        python tc4d7/tray.py
"""
import os
import sys

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
FLOOR = 4.0
LIFT = 12.0                 # floor top to board underside
WALL_H = LIFT - 1.0         # the wall stops 1 mm under the board: connectors overhanging the edge are clear
R_CORNER = 6.0
POST = (9.0, 4.2)           # OD, bore (M3 with +-0.6 mm for the estimated hole positions)
ROOT = 2.0                  # fillet where a post meets the floor
CBORE = (8.0, 3.2)          # head pocket under the floor: dia, depth (M3 socket head is 5.5 x 3)
VENT = (3.6, 7.0, 8.0)      # slot width, pitch, keep-out round each post column
SLOT = 44.0                 # slot length (y)

L, W = PCB[0] + 2 * (GAP + WALL), PCB[1] + 2 * (GAP + WALL)


def to_tray(x, y):
    """board top-left frame (y down) -> tray frame (centred, y up)."""
    return x - PCB[0] / 2, PCB[1] / 2 - y


def vents(posts):
    """a row of equal rounded slots across the floor under the board (along y), skipping the posts."""
    w, p, keep = VENT
    xs = [x for x in np.arange(-PCB[0] / 2 + 8, PCB[0] / 2 - 7, p)
          if all(abs(x - px) > keep for px, _ in posts)]
    return [(float(x), 0.0) for x in xs]


def post(p):
    """a post with a concave R ROOT fillet into the floor and a rounded top edge: one revolved profile."""
    r, a = POST[0] / 2, ROOT
    prof = (cq.Workplane("XZ").moveTo(0, FLOOR - 0.5).lineTo(r + a, FLOOR - 0.5).lineTo(r + a, FLOOR)
            .radiusArc((r, FLOOR + a), a).lineTo(r, FLOOR + LIFT - 0.8)
            .radiusArc((r - 0.8, FLOOR + LIFT), -0.8).lineTo(0, FLOOR + LIFT).close())
    return prof.revolve(360, (0, 0, 0), (0, 1, 0)).translate((p[0], p[1], 0))


def tray():
    pts = [to_tray(*h) for h in HOLES]
    t = cq.Workplane("XY").rect(L, W).extrude(FLOOR + WALL_H).edges("|Z").fillet(R_CORNER)
    t = t.cut(cq.Workplane("XY").workplane(offset=FLOOR).rect(L - 2 * WALL, W - 2 * WALL)
              .extrude(WALL_H + 1).edges("|Z").fillet(R_CORNER - WALL))
    t = t.faces(">Z").edges().fillet(WALL / 2 - 0.05)                  # full round on the wall top
    t = t.faces("<Z").edges().chamfer(0.6)
    for p in pts:
        t = t.union(post(p))
    t = t.cut(cq.Workplane("XY").pushPoints(pts).circle(POST[1] / 2).extrude(FLOOR + LIFT + 1))
    t = t.cut(cq.Workplane("XY").pushPoints(pts).circle(CBORE[0] / 2).extrude(CBORE[1]))
    t = t.cut(cq.Workplane("XY").pushPoints(vents(pts)).slot2D(SLOT, VENT[0], 90).extrude(FLOOR + 1))
    return t


def mesh(wp, name):
    path = os.path.join(OUT, name + ".stl")
    cq.exporters.export(wp, path, tolerance=0.02, angularTolerance=0.1)
    m = trimesh.load(path)
    print(f"{name:7s} {m.extents.round(1)}  watertight={m.is_watertight}  bodies={len(m.split())}")
    return m


def preview(m, path):
    """three studio renders (VTK, crab-arm/render_v2.py): tray, tray with the board, underside."""
    sys.path.insert(0, os.path.join(HERE, "..", "crab-arm"))
    import render_v2 as R
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    board = trimesh.creation.box((PCB[0], PCB[1], PCB[2]))
    board.apply_translation((0, 0, FLOOR + LIFT + PCB[2] / 2))
    white, pcb = (0.92, 0.92, 0.91), (0.13, 0.30, 0.24)
    views = [("tray", R._cam(215, 34, 300, (0, 0, 6)), [(m, white)]),
             ("with the board on its posts", R._cam(215, 26, 300, (0, 0, 10)), [(m, white), (board, pcb)]),
             ("underside: bolt heads sit in the floor", R._cam(205, -40, 300, (0, 0, 4)), [(m, white)])]
    fig, axs = plt.subplots(1, 3, figsize=(15, 4.4))
    for ax, (title, cam, scene) in zip(axs, views):
        ax.imshow(R.render(scene, cam, size=(900, 620)))
        ax.set_title(title, fontsize=11, color="#555")
        ax.set_axis_off()
    fig.tight_layout()
    fig.savefig(path, dpi=110)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    m = mesh(tray(), "tray")
    print(f"tray {L:.1f} x {W:.1f} x {FLOOR + LIFT:.1f}; {len(vents([to_tray(*h) for h in HOLES]))} vent slots; "
          f"board underside {FLOOR + LIFT:.1f} above the bed")
    preview(m, os.path.join(HERE, "preview.png"))
