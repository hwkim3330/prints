"""Two-part case for the Jetson Nano Developer Kit (B01 / A02 carrier, heatsink + fan on) (Bambu A1, PLA,
no supports, no screws, no clips).

  case_base.stl  floor + walls up to just over the ports, one clean window per port group on the front.
                 The board drops onto four square pegs in its corner holes (same as tray.py).
                 Printed floor-down.
  case_lid.stl   the cap over the heatsink and fan: a round-hole grille over the fan, rows of round holes
                 on the sides for the heatsink's exhaust. It sits on the base with a short skirt inside the
                 left and right walls and at the four corners (the ports and the heatsink take the middle of
                 the front and back). Printed top-down, so the top face is the smooth bed side.

The joint line is a deliberate groove (both edges chamfered); the bottom edge has a 1.2 mm chamfer so the
box looks like it floats a little. Outer corners R10.

Board data as in tray.py (SBC Model Framework "jetsonnano"); ports along y = 0 in board coordinates:
barrel jack x 2, HDMI/DP stack x 14, USB 3.0 stacks x 36 and 53, RJ45 x 68.5, micro-USB x 88.
FAN_TOP (PCB top -> top of the fan) is an estimate: the dev kit is 29 mm high from the PCB underside to the
heatsink top, plus a 10 mm fan. Measure it and set it before printing the lid.

Run:  uv run --with cadquery --with trimesh --with numpy --with scipy --with networkx --with manifold3d \\
        --with rtree --with matplotlib python case.py   ->  out/case_base.stl, out/case_lid.stl, out/case_preview.png
"""
import os

import cadquery as cq
import numpy as np
import trimesh

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
os.makedirs(OUT, exist_ok=True)

BW, BH = 100.0, 80.0
HOLES = [(x - BW / 2, y - BH / 2) for x, y in [(4, 17), (90, 17), (4, 75), (90, 75)]]
PCB_T = 1.6
CLEAR = 0.6
POCKET_R = 1.4                  # inner corner: a square-cornered board still fits
WALL = 2.52                     # 6 lines of 0.42
FLOOR = 2.0
STANDOFF_H = 5.0
STANDOFF_S = 7.0
PEG_S = 1.95
PEG_L = 2.4
CORNER = 10.0
BOTTOM_CHAMFER = 1.2
SEAM_CHAMFER = 0.6
TOP_CHAMFER = 1.2               # lid prints top-down: a chamfer, not a fillet, at the bed
FAN_TOP = float(os.environ.get("FAN_TOP", "38.0"))   # PCB top -> fan top (estimate, see above)
LID_GAP = 2.5                   # fan top -> lid underside
LID_T = 2.0
SKIRT_T = 1.26                  # 3 lines
SKIRT_H = 3.0
SKIRT_CLEAR = 0.2
CORNER_RETURN = 9.0             # skirt along the front/back walls from each corner
JOINT_OVER_PORTS = 3.0          # wall left above the tallest window

# front windows (board x from, board x to, height over the PCB top), each with MARGIN all round but the bottom
PORTS = [("barrel", 2.0, 11.0, 11.0), ("hdmi/dp", 14.0, 30.0, 14.5), ("usb x4", 36.0, 67.5, 16.0),
         ("rj45", 68.5, 84.5, 13.5), ("micro-usb", 88.0, 96.0, 3.5)]
MARGIN = 0.8
WIN_R = 1.0
SD_SLOT = (40.0, 7.0)           # back wall, under the module edge (microSD on the module underside), also exhaust
MODULE = (13.0, 33.0, 70.0, 45.0)   # board x, y, w, d of the module + heatsink footprint
HOLE_D, HOLE_P = 3.0, 5.0
# Camera ribbon (Arducam 8 MP IMX219, 15-pin 1 mm FFC): the CSI connectors are on the board's left edge
# (board y ~36); the ribbon leaves through a notch in the left wall at the joint, so the lid closes over it.
RIBBON = (24.0, 1.2, 47.0)      # notch width, depth, centre (board y)       # vent holes and their pitch

IW, ID = BW + 2 * CLEAR, BH + 2 * CLEAR
OW, OD = IW + 2 * WALL, ID + 2 * WALL
PCB_Z = FLOOR + STANDOFF_H
PCB_TOP = PCB_Z + PCB_T
JOINT = PCB_TOP + max(p[3] for p in PORTS) + MARGIN + JOINT_OVER_PORTS
LID_IN = PCB_TOP + FAN_TOP + LID_GAP           # lid underside
H = LID_IN + LID_T
LID_H = H - JOINT
MOD_C = (MODULE[0] + MODULE[2] / 2 - BW / 2, MODULE[1] + MODULE[3] / 2 - BH / 2)


def shell(z0, h):
    return cq.Workplane("XY").workplane(offset=z0).rect(OW, OD).extrude(h).edges("|Z").fillet(CORNER)


def pocket(z0, h, grow=0.0):
    return (cq.Workplane("XY").workplane(offset=z0).rect(IW + 2 * grow, ID + 2 * grow).extrude(h)
            .edges("|Z").fillet(POCKET_R + grow if grow > -POCKET_R else 0.3))


def hole_grid(w, h, pitch=HOLE_P):
    """Staggered grid of points filling a w x h rectangle, centred on 0."""
    pts, r = [], 0
    for y in np.arange(-h / 2, h / 2 + 1e-6, pitch * 0.866):
        off = pitch / 2 if r % 2 else 0.0
        for x in np.arange(-w / 2 + off, w / 2 + 1e-6, pitch):
            pts.append((float(x), float(y)))
        r += 1
    return pts


def base():
    b = shell(0, JOINT).faces("<Z").edges().chamfer(BOTTOM_CHAMFER).faces(">Z").edges().chamfer(SEAM_CHAMFER)
    b = b.cut(pocket(FLOOR, JOINT))
    b = b.union(cq.Workplane("XY").workplane(offset=FLOOR - 0.01).pushPoints(HOLES)
                .rect(STANDOFF_S, STANDOFF_S).extrude(STANDOFF_H + 0.01).edges("|Z").fillet(1.0))
    b = b.union(cq.Workplane("XY").workplane(offset=PCB_Z - 0.01).pushPoints(HOLES)
                .rect(PEG_S, PEG_S).extrude(PEG_L + 0.01).faces(">Z").edges().chamfer(0.4))
    for _, x0, x1, h in PORTS:
        w, hh = x1 - x0 + 2 * MARGIN, h + MARGIN
        b = b.cut(cq.Workplane("XZ").workplane(offset=OD / 2 - WALL - 1)      # XZ faces -y: front wall
                  .center((x0 + x1) / 2 - BW / 2, PCB_TOP + hh / 2).rect(w, hh).extrude(WALL + 2)
                  .edges("|Y").fillet(WIN_R))
    b = b.cut(cq.Workplane("XZ").workplane(offset=-OD / 2 - 1)
              .center(MOD_C[0], PCB_TOP + 1.0 + SD_SLOT[1] / 2).slot2D(*SD_SLOT).extrude(WALL + 2))
    b = b.cut(cq.Workplane("XY").workplane(offset=JOINT - RIBBON[1])
              .center(-OW / 2 + WALL / 2, RIBBON[2] - BH / 2).rect(WALL + 2, RIBBON[0]).extrude(5))
    # floor vents, hidden under the board, clear of the standoffs
    return b.cut(cq.Workplane("XY").workplane(offset=-1).pushPoints(hole_grid(70, 45)).circle(HOLE_D / 2)
                 .extrude(FLOOR + 2))


def lid():
    """Use orientation (sits on the base at z = JOINT)."""
    l = shell(JOINT, LID_H).faces(">Z").edges().chamfer(TOP_CHAMFER).faces("<Z").edges().chamfer(SEAM_CHAMFER)
    l = l.cut(pocket(JOINT - 1, LID_IN - JOINT + 1))
    ring = pocket(JOINT - SKIRT_H, SKIRT_H + 0.01, -SKIRT_CLEAR).cut(pocket(JOINT - SKIRT_H - 1, SKIRT_H + 2,
                                                                      -SKIRT_CLEAR - SKIRT_T))
    mid = IW - 2 * CORNER_RETURN
    ring = ring.cut(cq.Workplane("XY").workplane(offset=JOINT - SKIRT_H - 1).rect(mid, OD + 2).extrude(SKIRT_H + 2))
    ring = ring.cut(cq.Workplane("XY").workplane(offset=JOINT - SKIRT_H - 1)      # ribbon passes the skirt
                    .center(-IW / 2, RIBBON[2] - BH / 2).rect(6, RIBBON[0]).extrude(SKIRT_H + 2))
    l = l.union(ring)
    # top grille over the fan
    pts = [(MOD_C[0] + x, MOD_C[1] + y) for x, y in hole_grid(50, 50) if x * x + y * y <= 25 ** 2]
    l = l.cut(cq.Workplane("XY").workplane(offset=LID_IN - 1).pushPoints(pts).circle(HOLE_D / 2).extrude(LID_T + 2))
    # side vents: left, right and back, a band of holes at heatsink height
    band = (LID_H - LID_T - 6.0, 3)
    zc = JOINT + 3.0 + band[0] / 2
    rows = [zc + (i - 1) * HOLE_P * 0.866 for i in range(band[1])]
    def vent_pts(span):
        return [(x + (HOLE_P / 2 if k % 2 else 0), z) for k, z in enumerate(rows)
                for x in np.arange(-span / 2 + 2, span / 2 - 2 + 1e-6, HOLE_P)
                if abs(x + (HOLE_P / 2 if k % 2 else 0)) <= span / 2 - 2]
    side = vent_pts(ID - 2 * CORNER)
    for x0 in (OW / 2 - WALL - 1, -OW / 2 - 1):                              # right, left
        l = l.cut(cq.Workplane("YZ").workplane(offset=x0).pushPoints(side).circle(HOLE_D / 2).extrude(WALL + 2))
    return l.cut(cq.Workplane("XZ").workplane(offset=-OD / 2 - 1)            # back
                 .pushPoints(vent_pts(IW - 2 * CORNER)).circle(HOLE_D / 2).extrude(WALL + 2))


def mesh(wp):
    path = os.path.join(OUT, "_tmp.stl")
    cq.exporters.export(wp, path)
    m = trimesh.load(path)
    os.remove(path)
    return m


def box(size, centre):
    b = trimesh.creation.box(size)
    b.apply_translation(centre)
    return b


if __name__ == "__main__":
    bm, lm = mesh(base()), mesh(lid())
    pcb = box([BW, BH, PCB_T], [0, 0, PCB_Z + PCB_T / 2])
    for x, y in HOLES:
        h = trimesh.creation.cylinder(radius=1.5, height=PCB_T + 1)
        h.apply_translation([x, y, PCB_Z + PCB_T / 2])
        pcb = pcb.difference(h, engine="manifold")
    parts = {"pcb": pcb,
             "heatsink+fan": box([MODULE[2], MODULE[3], FAN_TOP], [MOD_C[0], MOD_C[1], PCB_TOP + FAN_TOP / 2]),
             "gpio": box([5.1, 51, 8.5], [94.5 - BW / 2, 45.5 - BH / 2, PCB_TOP + 4.25])}
    for name, x0, x1, h in PORTS:      # each port runs 12 mm in from the front edge and sticks out 1 mm
        parts[name] = box([x1 - x0, 13, h], [(x0 + x1) / 2 - BW / 2, -BH / 2 + 5.5, PCB_TOP + h / 2])
    probs = 0
    for n, m in parts.items():
        for o, om in (("base", bm), ("lid", lm)):
            v = trimesh.boolean.intersection([m, om], engine="manifold").volume
            if v > 0.05:
                print(f"  {n} hits {o} ({v:.1f} mm3)")
                probs += 1
    if trimesh.boolean.intersection([bm, lm], engine="manifold").volume > 0.05:
        print("  lid hits base")
        probs += 1
    print("clearance problems:", probs)
    print(f"case {OW:.1f} x {OD:.1f} x {H:.1f} mm, joint at z = {JOINT:.1f}, base {JOINT:.1f} + lid {LID_H:.1f}")

    lp = lm.copy()                                     # print top-down
    lp.apply_transform(trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0]))
    for name, m in (("case_base", bm), ("case_lid", lp)):
        m = m.copy()
        m.apply_translation([128 - m.bounds.mean(0)[0], 128 - m.bounds.mean(0)[1], -m.bounds[0][2]])
        m.export(os.path.join(OUT, name + ".stl"))
        print(f"{name:10s} {m.extents.round(1)} watertight={m.is_watertight}")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    def shade(m, c):
        k = np.clip(m.face_normals @ np.array([-.35, -.55, .76]), 0, 1) * 0.55 + 0.45
        return np.outer(k, matplotlib.colors.to_rgb(c))
    lifted = lm.copy()
    lifted.apply_translation([0, 0, 35])
    insides = [(pcb, "#2d6a4f"), (parts["heatsink+fan"], "#555555")] + \
              [(parts[p[0]], "#9a9a9a") for p in PORTS]
    fig = plt.figure(figsize=(18, 7), facecolor="white")
    views = [("closed (front)", 22, -70, [(bm, "#e8e6e1"), (lm, "#f2f1ee")]),
             ("closed (back)", 30, 115, [(bm, "#e8e6e1"), (lm, "#f2f1ee")]),
             ("open", 25, -60, [(bm, "#e8e6e1"), (lifted, "#f2f1ee")] + insides)]
    for k, (title, e, a, ms) in enumerate(views):
        ax = fig.add_subplot(1, 3, k + 1, projection="3d")
        for m, c in ms:
            ax.add_collection3d(Poly3DCollection(m.triangles, facecolors=shade(m, c)))
        ax.set_xlim(-60, 60); ax.set_ylim(-60, 60); ax.set_zlim(-10, 100 if k == 2 else 70)
        ax.set_box_aspect((1, 1, 0.92 if k == 2 else 0.67))
        ax.view_init(e, a); ax.set_axis_off(); ax.set_title(title)
    plt.tight_layout()
    plt.savefig(os.path.join(OUT, "case_preview.png"), dpi=75)
