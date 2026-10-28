"""PRINTED 2026-10-28 AND DID NOT FIT: fan height (FAN_TOP, an estimate) and the port openings were wrong on the
real board. Rebuild from NVIDIA's dev-kit 3D model / measured heights before printing again.

Two-part case for the Jetson Nano Developer Kit (B01 / A02 carrier, heatsink + fan on) with the Arducam
B0179 (IMX219 8 MP) looking out of the front, above the ports (Bambu A1, PLA, no supports, no bridges,
no screws, no clips).

  case_base.stl  a low tray: solid floor, walls up to just under the PCB top, the board drops onto four
                 square pegs in its corner holes (as tray.py). A 1.2 mm tongue on top of the left and right
                 walls (and the back corners) locates the lid. Printed floor-down.
  case_lid.stl   walls + top in one, printed upside down (the top is the smooth bed face). Every opening
                 that meets its bottom edge is a notch cut up from that edge (ports on the front,
                 microSD/exhaust at the back), so a notch's closed end is just a step: nothing to bridge.
                 Round-hole grille over the fan, rows of round holes high on the sides, the camera window
                 on the front and two rails inside the front wall, hanging from the ceiling.

Camera: slide the board up into the rails from the lid's open bottom (ribbon plugged in, lens to the
window) until it touches the ceiling; with the lid on, its bottom edge rests on the USB stacks, so it is
trapped between them and the ceiling. The rails grip it by its edges, so its screw holes don't matter.

Seam chamfered on both edges; 1.2 mm chamfer at the bottom and the top; outer corners R10.

Board data as in tray.py (SBC Model Framework "jetsonnano"); ports along y = 0 in board coordinates:
barrel jack x 2, HDMI/DP stack x 14, USB 3.0 stacks x 36 and 53, RJ45 x 68.5, micro-USB x 88.
Camera: the Raspberry Pi Camera v2 form factor (25 x 23.86 mm board, lens 9.46 mm below the top edge,
ribbon out of the bottom edge). FAN_TOP (PCB top -> top of the fan) is an estimate (dev kit 29 mm high from
the PCB underside to the heatsink top, plus a 10 mm fan); the camera already makes the box taller than that.

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
TOP_CHAMFER = 1.2               # chamfers, not fillets, at the bed
FAN_TOP = float(os.environ.get("FAN_TOP", "38.0"))   # PCB top -> fan top (estimate, see above)
FAN_GAP = 5.0                   # fan top -> ceiling, at least (FAN_TOP is an estimate)
TOP_T = 2.4
TONGUE = (1.2, 2.0)             # base wall tongue: thickness, height
TONGUE_CLEAR = 0.2
TONGUE_KEEP = 9.0               # tongue along the back wall from each corner
SEAM_DROP = 0.3                 # base/frame seam just under the PCB top

# front notches (board x from, board x to, height over the PCB top), MARGIN on the sides and top
PORTS = [("barrel", 2.0, 11.0, 11.0), ("hdmi/dp", 14.0, 30.0, 14.5), ("usb x4", 36.0, 67.5, 16.0),
         ("rj45", 68.5, 84.5, 13.5), ("micro-usb", 88.0, 96.0, 3.5)]
MARGIN = 0.7
WIN_R = 1.0
SD_SLOT = (40.0, 7.0)           # back wall, under the module edge (microSD on the module underside), also exhaust
MODULE = (13.0, 33.0, 70.0, 45.0)   # board x, y, w, d of the module + heatsink footprint
HOLE_D, HOLE_P = 3.0, 5.0       # vent holes and their pitch

CAM = (25.0, 23.86, 1.0)        # camera board w, h, thickness
CAM_LENS_TOP = 9.46             # lens centre below the board's top edge
CAM_LENS_H = 4.5                # lens block in front of the board
CAM_X = 0.0                     # camera centre (x); the ports below take the whole width anyway
CAM_WIN = 9.0                   # round window, outer edge chamfered
CAM_SLOT = 1.3                  # rail groove for the 1 mm board
CAM_GRIP = 1.5                  # how far the rails reach over the board's edges
CAM_ON_USB = 0.2                # camera board bottom edge above the USB stacks' top
CAM_TOP_GAP = 0.6               # camera board top edge -> ceiling

IW, ID = BW + 2 * CLEAR, BH + 2 * CLEAR
OW, OD = IW + 2 * WALL, ID + 2 * WALL
PCB_Z = FLOOR + STANDOFF_H
PCB_TOP = PCB_Z + PCB_T
JOINT = PCB_TOP - SEAM_DROP
NOTCH_TOP = PCB_TOP + max(p[3] for p in PORTS) + MARGIN
USB_TOP = PCB_TOP + [p[3] for p in PORTS if p[0] == "usb x4"][0]
CAM_Z = USB_TOP + CAM_ON_USB                    # camera board bottom edge, resting on the USB stacks
CAM_Y = -ID / 2 + CAM_LENS_H + 0.5              # camera board front face (lens 0.5 behind the wall)
LENS_Z = CAM_Z + CAM[1] - CAM_LENS_TOP
TOP_IN = max(PCB_TOP + FAN_TOP + FAN_GAP, CAM_Z + CAM[1] + CAM_TOP_GAP)   # ceiling
H = TOP_IN + TOP_T
RAIL_Z = NOTCH_TOP + 1.0                        # rails start over the USB notch
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


def blk(x0, x1, y0, y1, z0, z1):
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))


def tongue(z0, h, grow):
    """Ring on the inner half of the left/right walls and the back corners (the front has the ports, the
    back middle the microSD). grow > 0 gives the frame's matching rebate."""
    t = pocket(z0, h, TONGUE[0] + grow).cut(pocket(z0 - 1, h + 2, -1.0 if grow else 0.0))   # rebate: overlap the empty pocket, no coincident faces
    t = t.cut(cq.Workplane("XY").workplane(offset=z0 - 1).center(0, -OD / 2).rect(OW + 2, 12).extrude(h + 2))
    return t.cut(cq.Workplane("XY").workplane(offset=z0 - 1).center(0, OD / 2)
                 .rect(IW - 2 * TONGUE_KEEP, 2 * WALL + 6).extrude(h + 2))


def base():
    b = shell(0, JOINT).faces("<Z").edges().chamfer(BOTTOM_CHAMFER).faces(">Z").edges().chamfer(SEAM_CHAMFER)
    b = b.cut(pocket(FLOOR, JOINT))
    b = b.union(cq.Workplane("XY").workplane(offset=FLOOR - 0.01).pushPoints(HOLES)
                .rect(STANDOFF_S, STANDOFF_S).extrude(STANDOFF_H + 0.01).edges("|Z").fillet(1.0))
    b = b.union(cq.Workplane("XY").workplane(offset=PCB_Z - 0.01).pushPoints(HOLES)
                .rect(PEG_S, PEG_S).extrude(PEG_L + 0.01).faces(">Z").edges().chamfer(0.4))
    return b.union(tongue(JOINT - 0.01, TONGUE[1] + 0.01, 0.0))


def notch(wp, offset, x, w, top):
    """Opening cut up from the frame's bottom edge (z = JOINT) to z = top, rounded top corners."""
    n = (cq.Workplane(wp).workplane(offset=offset).center(x, (JOINT - 1 + top) / 2)
         .rect(w, top - JOINT + 1).extrude(WALL + 2))
    return n.edges("|X" if wp == "YZ" else "|Y").fillet(min(WIN_R, w / 2 - 0.01))


def cam_rails():
    """Two rails on the inside of the front wall, from the ceiling down to just over the USB notch. Each
    grips CAM_GRIP of the board edge from the front (a post from the wall) and the back (a post joined round
    the outside of the edge)."""
    r = None
    y0, yb = -ID / 2 - 0.5, CAM_Y + CAM_SLOT
    for s in (-1, 1):
        e = CAM_X + s * CAM[0] / 2                        # board edge
        xin, xout = e - s * CAM_GRIP, e + s * (CAM_SLOT - CAM[2] + 2.0)
        xa, xb = min(xin, xout), max(xin, xout)
        parts = [blk(xa, xb, y0, CAM_Y, RAIL_Z, TOP_IN + 0.5),                        # front post
                 blk(xa, xb, yb, yb + 1.6, RAIL_Z, TOP_IN + 0.5),                     # back post
                 blk(min(e + s * 0.3, xout), max(e + s * 0.3, xout), CAM_Y - 0.01, yb + 0.01,
                     RAIL_Z, TOP_IN + 0.5)]                                          # round the edge
        for p in parts:
            r = p if r is None else r.union(p)
    return r


def lid():
    """Use orientation (sits on the base at z = JOINT)."""
    f = (shell(JOINT, H - JOINT).faces("<Z").edges().chamfer(SEAM_CHAMFER)
         .faces(">Z").edges().chamfer(TOP_CHAMFER))
    f = f.cut(pocket(JOINT - 1, TOP_IN - JOINT + 1))
    f = f.cut(tongue(JOINT - 1, TONGUE[1] + TONGUE_CLEAR + 1, TONGUE_CLEAR))
    for _, x0, x1, h in PORTS:
        f = f.cut(notch("XZ", OD / 2 - WALL - 1, (x0 + x1) / 2 - BW / 2, x1 - x0 + 2 * MARGIN, PCB_TOP + h + MARGIN))
    f = f.cut(notch("XZ", -OD / 2 - 1, MOD_C[0], SD_SLOT[0], PCB_TOP + 1.0 + SD_SLOT[1]))
    f = f.union(cam_rails())
    f = f.cut(cq.Workplane("XZ").workplane(offset=OD / 2 - WALL - 1).center(CAM_X, LENS_Z)
              .circle(CAM_WIN / 2).extrude(WALL + 2))
    f = f.cut(cq.Workplane("XZ").workplane(offset=OD / 2 - 0.8).center(CAM_X, LENS_Z)          # outer chamfer
              .circle(CAM_WIN / 2).workplane(offset=1.6).circle(CAM_WIN / 2 + 1.6).loft())
    # side vents: left, right and back, three rows high up, level with the heatsink fins and the fan
    rows = [TOP_IN - 6.0 - i * HOLE_P * 0.866 for i in range(3)]

    def vent_pts(span):
        return [(x + (HOLE_P / 2 if k % 2 else 0), z) for k, z in enumerate(rows)
                for x in np.arange(-span / 2 + 2, span / 2 - 2 + 1e-6, HOLE_P)
                if abs(x + (HOLE_P / 2 if k % 2 else 0)) <= span / 2 - 2]
    side = vent_pts(ID - 2 * CORNER)
    for x0 in (OW / 2 - WALL - 1, -OW / 2 - 1):                              # right, left
        f = f.cut(cq.Workplane("YZ").workplane(offset=x0).pushPoints(side).circle(HOLE_D / 2).extrude(WALL + 2))
    f = f.cut(cq.Workplane("XZ").workplane(offset=-OD / 2 - 1)            # back
              .pushPoints(vent_pts(IW - 2 * CORNER)).circle(HOLE_D / 2).extrude(WALL + 2))
    pts = [(MOD_C[0] + x, MOD_C[1] + y) for x, y in hole_grid(50, 50) if x * x + y * y <= 25 ** 2]
    return f.cut(cq.Workplane("XY").workplane(offset=TOP_IN - 1).pushPoints(pts).circle(HOLE_D / 2)
                 .extrude(TOP_T + 2))


def mesh(wp):
    path = os.path.join(OUT, "_tmp.stl")
    cq.exporters.export(wp, path, tolerance=0.01, angularTolerance=0.05)
    m = trimesh.load(path)
    os.remove(path)
    return m


def box(size, centre):
    b = trimesh.creation.box(size)
    b.apply_translation(centre)
    return b


if __name__ == "__main__":
    bm, fm = mesh(base()), mesh(lid())
    pcb = box([BW, BH, PCB_T], [0, 0, PCB_Z + PCB_T / 2])
    for x, y in HOLES:
        h = trimesh.creation.cylinder(radius=1.5, height=PCB_T + 1)
        h.apply_translation([x, y, PCB_Z + PCB_T / 2])
        pcb = pcb.difference(h, engine="manifold")
    cam = box([CAM[0], CAM[2], CAM[1]], [CAM_X, CAM_Y + CAM[2] / 2, CAM_Z + CAM[1] / 2])
    lens = box([8.5, CAM_LENS_H, 8.5], [CAM_X, CAM_Y - CAM_LENS_H / 2, LENS_Z])
    parts = {"pcb": pcb, "camera board": cam, "lens": lens,
             "camera parts": box([CAM[0] - 2 * CAM_GRIP - 0.4, 2.5, CAM[1] - 1], [CAM_X, CAM_Y + CAM[2] + 1.25, CAM_Z + CAM[1] / 2]),
             "heatsink+fan": box([MODULE[2], MODULE[3], FAN_TOP], [MOD_C[0], MOD_C[1], PCB_TOP + FAN_TOP / 2]),
             "gpio": box([5.1, 51, 8.5], [94.5 - BW / 2, 45.5 - BH / 2, PCB_TOP + 4.25])}
    for name, x0, x1, h in PORTS:      # each port runs 12 mm in from the front edge and sticks out 1 mm
        parts[name] = box([x1 - x0, 13, h], [(x0 + x1) / 2 - BW / 2, -BH / 2 + 5.5, PCB_TOP + h / 2])
    shells = (("base", bm), ("lid", fm))
    probs = 0
    for n, m in parts.items():
        for o, om in shells:
            v = trimesh.boolean.intersection([m, om], engine="manifold").volume
            if v > 0.05:
                print(f"  {n} hits {o} ({v:.1f} mm3)")
                probs += 1
    for i in range(2):
        for j in range(i + 1, 2):
            if trimesh.boolean.intersection([shells[i][1], shells[j][1]], engine="manifold").volume > 0.05:
                print(f"  {shells[i][0]} hits {shells[j][0]}")
                probs += 1
    # the lens sees out: a ray from the lens straight ahead and 35 degrees to each side leaves the frame
    o = np.array([[CAM_X, CAM_Y - CAM_LENS_H, LENS_Z]])
    for d in ([0, -1, 0], [np.sin(.6), -np.cos(.6), 0], [-np.sin(.6), -np.cos(.6), 0], [0, -np.cos(.6), np.sin(.6)]):
        if len(fm.ray.intersects_location(o, np.array([d]))[0]):
            print("  camera view blocked along", np.round(d, 2))
            probs += 1
    print("clearance problems:", probs)
    print(f"case {OW:.1f} x {OD:.1f} x {H:.1f} mm; seam at z = {JOINT:.1f}; "
          f"lens at z = {LENS_Z:.1f}; fan clearance {TOP_IN - PCB_TOP - FAN_TOP:.1f} mm")

    flip = trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0])
    for name, m, f in (("case_base", bm, False), ("case_lid", fm, True)):
        m = m.copy()
        if f:
            m.apply_transform(flip)
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

    def up(m, dz):
        m = m.copy()
        m.apply_translation([0, 0, dz])
        return m
    insides = [(pcb, "#2d6a4f"), (parts["heatsink+fan"], "#555555"), (cam, "#2d6a4f"), (lens, "#111111")] + \
              [(parts[p[0]], "#9a9a9a") for p in PORTS]
    fig = plt.figure(figsize=(18, 7), facecolor="white")
    views = [("closed (front)", 18, -75, [(bm, "#e8e6e1"), (fm, "#f2f1ee")]),
             ("closed (back)", 30, 115, [(bm, "#e8e6e1"), (fm, "#f2f1ee")]),
             ("open", 25, -60, [(bm, "#e8e6e1"), (up(fm, 45), "#f2f1ee")] + insides)]
    for k, (title, e, a, ms) in enumerate(views):
        ax = fig.add_subplot(1, 3, k + 1, projection="3d")
        for m, c in ms:
            ax.add_collection3d(Poly3DCollection(m.triangles, facecolors=shade(m, c)))
        ax.set_xlim(-60, 60); ax.set_ylim(-60, 60); ax.set_zlim(-10, 130 if k == 2 else 70)
        ax.set_box_aspect((1, 1, 1.15 if k == 2 else 0.67))
        ax.view_init(e, a); ax.set_axis_off(); ax.set_title(title)
    plt.tight_layout()
    plt.savefig(os.path.join(OUT, "case_preview.png"), dpi=75)
