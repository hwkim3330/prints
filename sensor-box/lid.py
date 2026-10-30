"""Lid for the sensor box ("킹크랩"), carrying a robot arm: SO-ARM102 (lid-v2), SO-101 (lid-v1) or our own King Crab
arm (lid-v3, ARM=crab, ../crab-arm/).

The lid is the body's hexagon (240 across corners, R12 corners), 5 mm thick, printed top-face-down on the bed so the
top comes out flat and smooth; everything under it points up while printing, so no supports.

- Six posts under the corners sit on the body's corner columns and take an M3 screw each into the column pilots.
  They hold the lid 10 mm above the rim: that gap all round is the exhaust (the floor cable holes are the intake).
- lid-v2: SO-ARM102 follower (roboninecom/SO-ARM102, Sept 2026: PET-CF frame, parallel gripper, 352 deg base, 483 mm
  reach). Its 160 x 112.5 base has four 8.2 mm holes on an 80 x 80 square with a 10.2 mm counterbore from 10 mm up
  (made for desk C-clamps; the holes take M6 socket heads). The pan axis sits on the lid centre.
  4 x M6 x 25 socket head into M6 nuts trapped in bosses under the lid.
- lid-v1: SO-101 follower (TheRobotStudio/SO-ARM100), Base_SO101 with 4 x M4 x 30 countersunk into M4 nuts (its
  holes are 5 mm with a 10 mm countersink). The arm reaches forward (+y, through camera face 1).
- lid-v3: King Crab arm (../crab-arm/crab.py, 3 x MG996R + 2 x MG90S). Its turret's 100 x 100 flange takes
  4 x M4 x 20 into M4 nuts trapped under the lid at (+-40, +-40); a hole under the turret lets the J1 lead down.
- Ribs from the posts to the bosses carry the arm's load into the columns; a slot behind the arm takes its
  cable (servo bus board power + USB) down to the AGX.

Run:  uv run --with cadquery --with trimesh --with numpy --with scipy --with networkx --with manifold3d \\
        --with rtree --with matplotlib python sensor-box/lid.py
"""
import math
import os
import sys

import cadquery as cq
import numpy as np
import trimesh

import box

HERE = os.path.dirname(os.path.abspath(__file__))
ARM = os.environ.get("ARM", "so102")
VERSION = {"so102": "lid-v2", "so101": "lid-v1", "crab": "lid-v3", "lidar": "lid-lidar"}[ARM]
OUT = os.path.join(HERE, VERSION)
os.makedirs(OUT, exist_ok=True)
REF = os.path.join(HERE, "..", "ref-dl")       # downloaded arm STLs, not committed

T = 5.0                         # plate (= 12 lines; strong enough to spread the arm's moment into the ribs)
GAP = 10.0                      # lid underside above the rim: exhaust gap, and the posts' height
POST = 9.0                      # post across; sits on the column + lip + wall corner
RIB = (3.0, 7.0)                # width (~7 lines), height under the plate
M3 = (3.4, 6.5, 3.5)            # clearance, counterbore on top, counterbore depth
if ARM == "so102":
    # SO102.02.010 Base.stl: bottom at y = 0, x 0..160, z 0..112.5, pan axis (the 42 mm hole) at x 80, z 62.5
    ARM_HOLES = [(sx * 40.0, sy * 40.0) for sy in (1, -1) for sx in (-1, 1)]
    BASE_STL, ASSY_STL = os.path.join(REF, "so102", "base.stl"), None
    BASE_TF = [[1, 0, 0, -80.0], [0, 0, -1, 62.5], [0, 1, 0, 0], [0, 0, 0, 1]]   # x - 80, -(z - 62.5), y
    NUT = (6.5, 10.27, 5.2)     # M6: clearance, nut across flats (+0.27), pocket depth (nut 5.0)
    BOSS = 18.0
    CABLE_Y = -80.0             # the base covers y -50..62.5 (mirrored z)
elif ARM == "crab":
    # King Crab arm (../crab-arm/crab.py): its turret's 100 x 100 flange, M4 at (+-40, +-40), yaw axis on the lid centre.
    # The J1 servo stands in the turret with its lead going straight down through a hole under it.
    ARM_HOLES = [(sx * 40.0, sy * 40.0) for sy in (1, -1) for sx in (-1, 1)]
    BASE_STL, ASSY_STL = "crab", None
    BASE_TF = np.eye(4).tolist()                # the turret is built in use orientation, bottom at z = 0
    NUT = (4.5, 7.27, 3.4)      # M4
    BOSS = 14.0
    CABLE_Y = -62.0             # the flange ends at y -50
    J1_LEAD = (14.0, 26.0, -13.0)   # x size, y size, centre y: under the J1 case, inside the turret
elif ARM == "lidar":
    # Temporary lidar lid (Ouster OS1, Ø85 x 73.5) until the real mount is settled. The OS1's own M3 pattern is only in
    # Ouster's drawing, so eight radial M3 slots (r 18..40) take any bolt circle or square inside the base. The four
    # M5 bosses at (+-60, +-60) are the REV9 OS1 plate pattern (P05, 140 x 140 x 5 AL6061): that aluminium plate bolts
    # on later as the heat sink the OS1 manual asks for -- PLA under the sensor is for short trials only.
    ARM_HOLES = [(sx * 60.0, sy * 60.0) for sy in (1, -1) for sx in (-1, 1)]
    BASE_STL, ASSY_STL = "", None
    BASE_TF = np.eye(4).tolist()
    NUT = (5.5, 8.27, 4.2)      # M5: clearance, nut across flats (+0.27), pocket depth (nut 4.0)
    BOSS = 14.0
    CABLE_Y = -82.0             # outside the 140 mm plate (y -70)
    LIDAR = dict(d=85.0, h=73.5, ring=86.0, ring_depth=1.0, slots=(18.0, 40.0, 3.4), n=8, vent=30.0)
else:
    # Base_SO101.stl: bottom at y = 0, x across, z front-to-back; the narrow pair (x +-27.8) on the reach side
    ARM_HOLES = [(sx * 27.8, 34.9) for sx in (-1, 1)] + [(sx * 31.8, -34.8) for sx in (-1, 1)]
    BASE_STL = os.path.join(REF, "SO-ARM100", "STL", "SO101", "Individual", "Base_SO101.stl")
    ASSY_STL = os.path.join(REF, "SO-ARM100", "STL", "SO101", "Individual", "SO101 Assembly.stl")
    BASE_TF = [[-1, 0, 0, 0], [0, 0, 1, -27.6], [0, 1, 0, 0], [0, 0, 0, 1]]      # -x, z - 27.6 (centres the plate), y
    NUT = (4.5, 7.27, 3.4)      # M4
    BOSS = 14.0
    CABLE_Y = -60.0             # the base ends at y -43.5
CABLE = (34.0, 14.0, CABLE_Y)  # slot length, width (round ends), centre y: behind the arm base
NAME = ("킹크랩", 14.0, 0.6, 86.0 if ARM == "lidar" else 72.0)   # text, size, depth, centre y (in front of the arm / plate)
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
    p = p.cut(cq.Workplane("XY").pushPoints(hs).circle(NUT[0] / 2).extrude(top + 1))
    p = p.cut(cq.Workplane("XY").workplane(offset=under - 0.01).pushPoints(hs).polygon(6, NUT[1] / math.cos(math.radians(30)))
              .extrude(NUT[2]))
    w, l, y = CABLE
    p = p.cut(cq.Workplane("XY").center(0, y).slot2D(w, l).extrude(top + 1))      # round ends (r = l / 2)
    if ARM == "crab":
        w, l, y = J1_LEAD
        p = p.cut(cq.Workplane("XY").center(0, y).rect(w, l).extrude(top + 1).edges("|Z").fillet(3))
    if ARM == "lidar":
        L = LIDAR
        p = p.cut(cq.Workplane("XY").workplane(offset=top - L["ring_depth"]).circle(L["ring"] / 2).extrude(2))
        p = p.cut(cq.Workplane("XY").circle(L["vent"] / 2).extrude(top + 1))
        r0, r1, w = L["slots"]
        for k in range(L["n"]):          # off the axes, so no slot lands on the rib along x
            a = math.radians(22.5 + 360 / L["n"] * k)
            c = ((r0 + r1) / 2 * math.cos(a), (r0 + r1) / 2 * math.sin(a))
            p = p.cut(cq.Workplane("XY").center(*c).slot2D(r1 - r0 + w, w, math.degrees(a)).extrude(top + 1))
    txt, size, depth, ty = NAME
    p = p.cut(cq.Workplane("XY").workplane(offset=top - depth).center(0, ty)
              .text(txt, size, depth + 1, fontPath=FONT, halign="center", valign="center"))
    return p


def place_base(m):
    """The arm's base STL (its bottom at y = 0) onto the lid top."""
    m = m.copy()
    tf = np.array(BASE_TF, float)
    tf[2, 3] = GAP + T
    m.apply_transform(tf)
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

    # the arm's base: its holes must line up with ours, it must sit on the plate and stay inside the lid's outline
    parts = []
    if ARM == "crab":
        sys.path.insert(0, os.path.join(HERE, "..", "crab-arm"))
        import crab
    if ARM in ("crab", "lidar") or os.path.exists(BASE_STL):
        if ARM == "lidar":                  # the OS1 as a plain cylinder resting on the floor of its locating ring
            base = trimesh.creation.cylinder(radius=LIDAR["d"] / 2, height=LIDAR["h"], sections=96)
            base.apply_translation((0, 0, LIDAR["h"] / 2 - LIDAR["ring_depth"] + 0.01))
            base = place_base(base)
        else:
            base = place_base(box.mesh(crab.turret()) if ARM == "crab" else trimesh.load(BASE_STL))
        print("base on lid: x", base.bounds[:, 0].round(1), "y", base.bounds[:, 1].round(1), "z", base.bounds[:, 2].round(1))
        for h in ARM_HOLES:
            o = np.array([[h[0] + (NUT[0] / 2 - 0.6) * math.cos(a), h[1] + (NUT[0] / 2 - 0.6) * math.sin(a), GAP + T + 40] for a in np.linspace(0, 6.2, 12)])
            if base.ray.intersects_any(o, np.tile([0, 0, -1.0], (len(o), 1))).any():
                print(f"  bolt at {h} is blocked by the base")
                probs += 1
            if lm.ray.intersects_any(o, np.tile([0, 0, -1.0], (len(o), 1))).any():
                print(f"  bolt at {h} is blocked in the lid")
                probs += 1
        if trimesh.boolean.intersection([base, lm], engine="manifold").volume > 0.01:
            print("  base overlaps the lid")
            probs += 1
        foot = base.vertices[base.vertices[:, 2] < GAP + T + 0.5][:, :2]
        if any(np.abs(foot @ [math.cos(box.phi(i)), math.sin(box.phi(i))]).max() > box.APO - 3 for i in range(3)):
            print("  the base hangs over the lid's edge")
            probs += 1
        w, l, y = CABLE
        if base.bounds[0, 1] < y + l / 2 + 2:
            print("  cable slot is under the base")
            probs += 1
        parts.append(("base", base))
        if ASSY_STL and os.path.exists(ASSY_STL):
            a = trimesh.load(ASSY_STL)     # assembly frame: z up, base bottom z = 0, reaching -y; holes at y 45.2/-24.5
            a.apply_transform(np.array([[-1, 0, 0, 0], [0, -1, 0, 10.4], [0, 0, 1, GAP + T], [0, 0, 0, 1]], float))
            parts.append(("arm", a))
        if ARM == "crab":                   # the arm at its home pose, for the preview
            ch = crab.chain(crab.POSES["home (upright, forearm forward)"])
            for n, (wp, fr) in crab.build().items():
                if fr != "W":
                    a = box.mesh(wp)
                    a.apply_transform(ch[fr])
                    a.apply_translation((0, 0, GAP + T))
                    parts.append(("arm", a))
    else:
        print(f"  ({BASE_STL} not found: download the arm's base STL into ../ref-dl to check it)")
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
