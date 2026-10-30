"""Lid for the sensor box ("킹크랩"), carrying an SO-101 robot arm.

The lid is the body's hexagon (240 across corners, R12 corners), 5 mm thick, printed top-face-down on the bed so the
top comes out flat and smooth; everything under it points up while printing, so no supports.

- Six posts under the corners sit on the body's corner columns and take an M3 screw each into the column pilots.
  They hold the lid 10 mm above the rim: that gap all round is the exhaust (the floor cable holes are the intake).
- The arm is the open SO-101 follower (TheRobotStudio/SO-ARM100, STS3215 servos), its Base_SO101 bolted on with
  4 x M4 x 30 countersunk screws into hex nuts trapped in bosses under the lid. The base's own holes are
  countersunk for that (5 mm hole, 10 mm countersink). The arm reaches forward (+y, through camera face 1).
- Ribs from the posts to the bosses carry the arm's load into the columns; a slot behind the arm takes its
  cable (servo bus board power + USB) down to the AGX.

Run:  uv run --with cadquery --with trimesh --with numpy --with scipy --with networkx --with manifold3d \\
        --with rtree --with matplotlib python sensor-box/lid.py
"""
import math
import os

import cadquery as cq
import numpy as np
import trimesh

import box

HERE = os.path.dirname(os.path.abspath(__file__))
VERSION = "lid-v1"
OUT = os.path.join(HERE, VERSION)
os.makedirs(OUT, exist_ok=True)
SO101 = os.path.join(HERE, "..", "ref-dl", "SO-ARM100", "STL", "SO101", "Individual")   # not committed

T = 5.0                         # plate (= 12 lines; strong enough to spread the arm's moment into the ribs)
GAP = 10.0                      # lid underside above the rim: exhaust gap, and the posts' height
POST = 9.0                      # post across; sits on the column + lip + wall corner
RIB = (3.0, 7.0)                # width (~7 lines), height under the plate
M3 = (3.4, 6.5, 3.5)            # clearance, counterbore on top, counterbore depth
# SO-101 base holes (from Base_SO101.stl, its bottom at y = 0, x across, z front-to-back), placed here with the arm
# reaching +y: the narrow pair (x +-27.8) on the reach side, the wide pair (x +-31.8) behind
ARM_HOLES = [(sx * 27.8, 34.9) for sx in (-1, 1)] + [(sx * 31.8, -34.8) for sx in (-1, 1)]
BASE_Z0 = 27.6                  # base z that lands on lid y = 0 (centres the 87 mm base plate)
BOSS = 14.0
M4 = (4.5, 7.27, 3.4)           # clearance, nut across flats (+0.27), nut pocket depth (nut 3.2)
CABLE = (34.0, 14.0, 7.0, -60.0)  # slot x, y, corner radius, centre y (behind the arm base, base ends at y -43.5)
NAME = ("킹크랩", 14.0, 0.6, 72.0)   # text, size, depth, centre y (in front of the arm)
FONT = "/System/Library/Fonts/Supplemental/AppleGothic.ttf"


def corners():
    """The body's lid pilots (corner column centres), as in box.body()."""
    ri = box.L - box.WALL / math.cos(math.radians(30))
    return [((ri - box.COL / 2) * math.cos(math.radians(60 * k)), (ri - box.COL / 2) * math.sin(math.radians(60 * k)))
            for k in range(6)]


def bar(p, q, w, h, z0):
    p, q = np.array(p), np.array(q)
    d = q - p
    c = (p + q) / 2
    return (cq.Workplane("XY").workplane(offset=z0).center(*c).rect(float(np.linalg.norm(d)), w).extrude(h)
            .rotate((c[0], c[1], 0), (c[0], c[1], 1), math.degrees(math.atan2(d[1], d[0]))))


def lid():
    """In use orientation: plate from z = GAP to GAP + T, posts and ribs below it, z = 0 on the body's rim."""
    p = (cq.Workplane("XY").workplane(offset=GAP).polygon(6, 2 * box.L).extrude(T).edges("|Z").fillet(box.FILLET)
         .faces(">Z").edges().chamfer(1.0))
    cs = corners()
    for c in cs:
        p = p.union(cq.Workplane("XY").center(*c).rect(POST, POST).extrude(GAP + 0.1)
                    .rotate((c[0], c[1], 0), (c[0], c[1], 1), math.degrees(math.atan2(c[1], c[0]))))
    under = GAP - RIB[1]
    # ribs: each corner post to the nearest arm boss, the bosses round in a ring, and across the middle
    hs = ARM_HOLES
    ring = [hs[0], hs[1], hs[3], hs[2]]
    for c in cs:
        h = min(hs, key=lambda q: math.dist(q, c))
        p = p.union(bar(c, h, RIB[0], RIB[1], under))
    for a, b in zip(ring, ring[1:] + ring[:1]):
        p = p.union(bar(a, b, RIB[0], RIB[1], under))
    p = p.union(bar(cs[0], cs[3], RIB[0], RIB[1], under))
    for h in hs:
        p = p.union(cq.Workplane("XY").workplane(offset=under).center(*h).circle(BOSS / 2).extrude(RIB[1]))
    # holes
    top = GAP + T
    p = p.cut(cq.Workplane("XY").pushPoints(cs).circle(M3[0] / 2).extrude(top + 1))
    p = p.cut(cq.Workplane("XY").workplane(offset=top - M3[2]).pushPoints(cs).circle(M3[1] / 2).extrude(M3[2] + 1))
    p = p.cut(cq.Workplane("XY").pushPoints(hs).circle(M4[0] / 2).extrude(top + 1))
    p = p.cut(cq.Workplane("XY").workplane(offset=under - 0.01).pushPoints(hs).polygon(6, M4[1] / math.cos(math.radians(30)))
              .extrude(M4[2]))
    w, l, r, y = CABLE
    p = p.cut(cq.Workplane("XY").center(0, y).slot2D(w, l).extrude(top + 1))      # round ends (r = l / 2)
    txt, size, depth, ty = NAME
    p = p.cut(cq.Workplane("XY").workplane(offset=top - depth).center(0, ty)
              .text(txt, size, depth + 1, fontPath=FONT, halign="center", valign="center"))
    return p


def place_base(m):
    """Base_SO101 onto the lid top. Its frame: x across, y up (bottom y = 0), z front-to-back with the narrow hole
    pair at z = 62.5 on the reach side. Lid frame: reach = +y, so (x, y, z) -> (-x, z - BASE_Z0, y + top)."""
    m = m.copy()
    R = np.array([[-1, 0, 0, 0], [0, 0, 1, -BASE_Z0], [0, 1, 0, GAP + T], [0, 0, 0, 1]], float)
    m.apply_transform(R)
    return m


if __name__ == "__main__":
    lw = lid()
    lm = box.mesh(lw)
    print(f"lid {lm.extents.round(1)}  watertight={lm.is_watertight}  volume {lm.volume / 1000:.0f} cm3")
    probs = 0

    # the lid on the body: posts must land on solid rim, nothing else may touch the body
    bm = box.mesh(box.body())
    on = lm.copy()
    on.apply_translation([0, 0, box.H])
    inter = trimesh.boolean.intersection([on, bm], engine="manifold")
    if inter.volume > 0.01:
        print(f"  lid overlaps the body: {inter.volume:.2f} mm3")
        probs += 1
    # each post's footprint: how much of it rests on the rim (body top within 0.2 mm below)
    for c in corners():
        g = np.array([(c[0] + dx, c[1] + dy, box.H + 1) for dx in np.linspace(-POST / 2 + .5, POST / 2 - .5, 9)
                      for dy in np.linspace(-POST / 2 + .5, POST / 2 - .5, 9)])
        loc, idx, _ = bm.ray.intersects_location(g, np.tile([0, 0, -1.0], (len(g), 1)), multiple_hits=False)
        frac = (loc[:, 2] > box.H - 0.3).sum() / len(g)
        if frac < 0.6:
            print(f"  post at {np.round(c, 1)} rests only {frac:.0%} on the rim")
            probs += 1

    # the SO-101 base: its holes must line up with ours, and it must sit flat on the plate
    parts = []
    bp = os.path.join(SO101, "Base_SO101.stl")
    if os.path.exists(bp):
        base = place_base(trimesh.load(bp))
        print("base on lid: x", base.bounds[:, 0].round(1), "y", base.bounds[:, 1].round(1), "z", base.bounds[:, 2].round(1))
        for h in ARM_HOLES:
            o = np.array([[h[0] + 1.6 * math.cos(a), h[1] + 1.6 * math.sin(a), GAP + T + 40] for a in np.linspace(0, 6.2, 12)])
            if base.ray.intersects_any(o, np.tile([0, 0, -1.0], (len(o), 1))).any():
                print(f"  M4 at {h} is blocked by the base")
                probs += 1
            if lm.ray.intersects_any(o, np.tile([0, 0, -1.0], (len(o), 1))).any():
                print(f"  M4 at {h} is blocked in the lid")
                probs += 1
        if trimesh.boolean.intersection([base, lm], engine="manifold").volume > 0.01:
            print("  base overlaps the lid")
            probs += 1
        w, l, r, y = CABLE
        if base.bounds[0, 1] < y + l / 2 + 2:
            print("  cable slot is under the base")
            probs += 1
        parts.append(("base", base))
        ap = os.path.join(SO101, "SO101 Assembly.stl")
        if os.path.exists(ap):
            a = trimesh.load(ap)     # assembly frame: z up, base bottom z = 0, reaching -y; holes at y 45.2/-24.5
            a.apply_transform(np.array([[-1, 0, 0, 0], [0, -1, 0, 10.4], [0, 0, 1, GAP + T], [0, 0, 0, 1]], float))
            parts.append(("arm", a))
    else:
        print("  (SO-101 STLs not found: git clone TheRobotStudio/SO-ARM100 into ../ref-dl to check the arm)")
    print("clearance problems:", probs)

    # print orientation: top face down
    pm = lm.copy()
    pm.apply_transform(trimesh.transformations.rotation_matrix(math.pi, [1, 0, 0]))
    pm.apply_translation([128 - pm.bounds.mean(0)[0], 128 - pm.bounds.mean(0)[1], -pm.bounds[0][2]])
    pm.export(os.path.join(OUT, "lid.stl"))
    asm = [("body", bm), ("lid", on)]
    for n, m in parts:
        m = m.copy()
        m.apply_translation([0, 0, box.H])
        asm.append((n, m))
    trimesh.util.concatenate([m for n, m in asm if n != "arm"]).export(   # the arm alone is 40 MB: preview only
os.path.join(OUT, "assembly.stl"))

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    col = {"body": "#d9a441", "lid": "#e8e2d0", "base": "#c0392b", "arm": "#c0392b"}

    def shade(m, c):
        k = np.clip(m.face_normals @ np.array([-.4, -.5, .8]), 0, 1) * 0.6 + 0.4
        return np.outer(k, matplotlib.colors.to_rgb(c))
    fig = plt.figure(figsize=(16, 7))
    views = [(asm, 18, -60, (-160, 160), (-60, 450)), ([("lid", pm.copy())], 65, -90, None, None)]
    for k, (ms, e, az, xy, zl) in enumerate(views):
        ax = fig.add_subplot(1, 2, k + 1, projection="3d")
        for n, m in ms:
            ax.add_collection3d(Poly3DCollection(m.triangles, facecolors=shade(m, col[n])))
        if xy:
            ax.set_xlim(*xy); ax.set_ylim(-250, 250); ax.set_zlim(*zl)
            ax.set_box_aspect((320, 500, 510))
        else:
            c = ms[0][1].bounds.mean(0)
            ax.set_xlim(c[0] - 125, c[0] + 125); ax.set_ylim(c[1] - 125, c[1] + 125); ax.set_zlim(0, 60)
            ax.set_box_aspect((250, 250, 60))
        ax.view_init(e, az); ax.set_axis_off()
    plt.tight_layout()
    plt.savefig(os.path.join(OUT, "preview.png"), dpi=65)
