"""SCOUT MINI sensor box, print version: one-piece hexagonal body for the Bambu Lab A1, PLA, open top.

Body: hexagon 240 mm across corners (fits the 256 mm bed), 208 across flats, 130 tall, 2.5 mm walls,
3.2 mm floor, 45 deg fillets at the floor and a 45 deg lip at the top, printed floor-down without supports in one ~5 h job. One camera per face (60 deg apart).
Corner columns inside stiffen the walls and carry pilot holes for a lid later (lidar not decided).
Rail bars are a separate small print.

Camera (measured): red holder 40.16 x 35.03 x 3.51 sits in the wall window, the clear housing
31.74 x 30.25 (10.9 proud, flush with the red holder's top edge) goes out through the wall, M2 screws at 34.1 x 29.0 from outside.
The camera mounts straight on the wall: the red holder sits in a 1 mm pocket inside a 4 mm pad, the
clear housing goes out through an opening, 4 x M2 x 6 from outside. No separate plates.

Design source: github.com/hwkim3330/scout-mini-sensor-box (REV9 sheet-metal box, rev10p panel version).
Run:  uv run --with cadquery --with trimesh --with numpy --with scipy --with networkx --with manifold3d \\
        --with rtree --with matplotlib python sensor-box/box.py
"""
import math
import os

import cadquery as cq
import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
VERSION = "v6"                  # output folder; bump it for a new version and keep the old ones
OUT = os.path.join(HERE, VERSION)
os.makedirs(OUT, exist_ok=True)

L = 120.0                       # hexagon side = circumradius (240 across corners)
APO = L * math.sqrt(3) / 2      # 103.9
H = 130.0
WALL = 2.5                      # = 6 lines of 0.42 (3 walls each side): no slow gap fill
FLOOR = 3.2
FOOT = 7.0                      # 45 deg fillet strip inside where the walls meet the floor
LIP = 5.0                       # 45 deg inward lip around the top: stiffens the rim, seat for a lid
FILLET = 12.0                   # outer vertical corners: soft look, and big round corners lift less than sharp ones
COL = 7.0                       # inner corner column, measured along each wall
PILOT = 2.6                     # M3 self-tapping
CLEAR3 = 3.4

# camera (measured 2026-10-27)
CAM_Z = 92.0
RED = (40.16, 35.03, 3.51)
CLEARP = (31.74, 30.25, 10.9)
CAM_WIN = (RED[0] + 0.8, RED[1] + 0.8)
# The camera mounts straight on the wall (no separate plate): the clear housing goes out through an
# opening, the red holder sits in a 1 mm pocket on the inside, 4 x M2 x 6 from outside into the red holder.
PAD = (CAM_WIN[0] + 8, CAM_WIN[1] + 8, 4.0)   # wall thickened to 4 mm around the camera, inside
CAM_T = 3.0                     # wall left at the opening; the pocket is the last PAD[2] - CAM_T
CAM_CUT = (CLEARP[0] + 0.6, CLEARP[1] + 0.6)
CLEAR_DY = (RED[1] - CLEARP[1]) / 2   # the clear housing is flush with the red holder's top edge (cable side down)
M2_PITCH = (31.90 + 2.2, 26.8 + 2.2)
M2_HOLES = [(sx * M2_PITCH[0] / 2, sz * M2_PITCH[1] / 2) for sx in (-1, 1) for sz in (-1, 1)]
M2_CLEAR = 2.4

# vents: low intake, the open top is the exhaust
VENT_W, VENT_H, VENT_PITCH, VENT_Z, VENT_N = 5.0, 24.0, 10.0, 18.0, 7

# floor
GRID = 20.0
AGX_C = (0.0, 15.0)
AGX_SO = [(AGX_C[0] + sx * 45, AGX_C[1] + sy * 45) for sx in (-1, 1) for sy in (-1, 1)]
AGX_BOX = (110.0, 110.0, 72.0)

# rail bars (HOLD: rail pitch, the slots take +-12 mm)
RAIL_X = 115.0
RAIL_SLOT = (5.5, 24.0)
BAR = (248.0, 30.0, 8.0)
BAR_Y = 60.0
BAR_BOLTS_X = (-80.0, -40.0, 40.0, 80.0)
M4 = 4.5


def phi(i):
    return math.radians(30 + 60 * i)


def face(i):
    """4x4: face-local (x across, y up from the floor bottom, z inwards from the outer face) -> world."""
    p = phi(i)
    n = np.array([math.cos(p), math.sin(p), 0.0])
    t = np.array([math.sin(p), -math.cos(p), 0.0])
    m = np.eye(4)
    m[:3, 0], m[:3, 1], m[:3, 2] = t, (0, 0, 1), -n
    m[:3, 3] = n * APO
    return m


def on_face(i, wp):
    """Place a solid built in face-local coordinates (XY = face plane, +Z inwards) onto face i."""
    m = face(i)
    ang = math.degrees(math.atan2(m[1, 0], m[0, 0]))
    # local x -> t, local y -> world z, local z -> -n : rotate X by 90 (y->z, z->-y), then about Z
    s = wp.rotate((0, 0, 0), (1, 0, 0), 90).rotate((0, 0, 0), (0, 0, 1), ang)
    return s.translate(tuple(m[:3, 3]))


def body():
    b = cq.Workplane("XY").polygon(6, 2 * L).extrude(H).edges("|Z").fillet(FILLET)
    inner = cq.Workplane("XY").workplane(offset=FLOOR).polygon(6, 2 * (L - WALL / math.cos(math.radians(30)))).extrude(H)
    b = b.cut(inner)
    ri = L - WALL / math.cos(math.radians(30))          # inner circumradius
    for k in range(6):                                  # inner corner columns
        a = math.radians(60 * k)
        v = np.array([ri * math.cos(a), ri * math.sin(a)])
        u1 = np.array([math.cos(a + math.radians(120)), math.sin(a + math.radians(120))])
        u2 = np.array([math.cos(a - math.radians(120)), math.sin(a - math.radians(120))])
        pts = [v, v + COL * u1, v + COL * (u1 + u2), v + COL * u2]
        col = cq.Workplane("XY").polyline([tuple(p) for p in pts]).close().extrude(H)
        c = v + COL * (u1 + u2) / 2
        b = b.union(col).cut(cq.Workplane("XY").workplane(offset=H - 12).center(*c).circle(PILOT / 2).extrude(13))
    li = ri                                             # inner side length (= inner circumradius)
    for i in range(6):
        # fillet strip at the floor and a lip at the top, both 45 deg so they print without supports
        foot = (cq.Workplane("YZ").polyline([(FLOOR, WALL), (FLOOR, WALL + FOOT), (FLOOR + FOOT, WALL)]).close()
                .extrude(li / 2, both=True))
        lip = (cq.Workplane("YZ").polyline([(H - LIP, WALL), (H, WALL), (H, WALL + LIP)]).close()
               .extrude(li / 2, both=True))
        b = b.union(on_face(i, foot)).union(on_face(i, lip))
    b = b.faces("<Z").edges().chamfer(0.5)              # no elephant foot on the first layer
    for i in range(6):
        b = camera_mount(b, lambda wp: on_face(i, wp))
        for j in range(VENT_N):
            x = (j - (VENT_N - 1) / 2) * VENT_PITCH
            v = (cq.Workplane("XY").center(x, VENT_Z + VENT_H / 2).rect(VENT_W, VENT_H).extrude(WALL + 2)
                 .translate((0, 0, -1)).edges("|Z").fillet(VENT_W / 2 - 0.01))
            b = b.cut(on_face(i, v))
    # floor holes: M3 grid, AGX pattern, M4 to the rail bars
    grid = []
    r = APO - WALL - 14
    for gx in np.arange(-200, 201, GRID):
        for gy in np.arange(-200, 201, GRID):
            if all(abs(gx * math.cos(phi(i)) + gy * math.sin(phi(i))) < r for i in range(3)):
                if all(abs(gy - sy * BAR_Y) > BAR[1] / 2 + 3 for sy in (-1, 1)):
                    grid.append((gx, gy))
    b = b.cut(cq.Workplane("XY").pushPoints(grid + AGX_SO).circle(CLEAR3 / 2).extrude(FLOOR))
    bolts = [(x, sy * BAR_Y) for x in BAR_BOLTS_X for sy in (-1, 1)]
    return b.cut(cq.Workplane("XY").pushPoints(bolts).circle(M4 / 2).extrude(FLOOR))


def camera_mount(b, place):
    """Pad, pocket for the red holder, opening for the clear housing and M2 holes, in face-local
    coordinates (XY on the outer face, +Z inwards) mapped by `place`."""
    cz = CAM_Z
    b = b.union(place(cq.Workplane("XY").center(0, cz).rect(PAD[0], PAD[1]).extrude(PAD[2])))
    b = b.cut(place(cq.Workplane("XY").workplane(offset=CAM_T).center(0, cz).rect(*CAM_WIN)
                    .extrude(PAD[2]).edges("|Z").fillet(1)))
    b = b.cut(place(cq.Workplane("XY").center(0, cz + CLEAR_DY).rect(*CAM_CUT).extrude(PAD[2] + 2)
                    .translate((0, 0, -1))))
    return b.cut(place(cq.Workplane("XY").pushPoints([(x, cz + y) for x, y in M2_HOLES]).circle(M2_CLEAR / 2)
                       .extrude(PAD[2] + 2).translate((0, 0, -1))))


def cam_test():
    """The camera mount cut out of a 4 mm wall piece, printed outer face down: fit the camera before the body."""
    w = PAD[0] + 10
    t = cq.Workplane("XY").center(0, CAM_Z).rect(w, PAD[1] + 10).extrude(WALL)
    return camera_mount(t, lambda wp: wp)


def rail_bar():
    b = cq.Workplane("XY").box(*BAR, centered=(True, True, False)).edges("|Z").fillet(4)
    b = b.cut(cq.Workplane("XY").pushPoints([(x, 0) for x in BAR_BOLTS_X]).circle(M4 / 2).extrude(BAR[2]))
    b = b.cut(cq.Workplane("XY").pushPoints([(x, 0) for x in BAR_BOLTS_X]).polygon(6, 8.1).extrude(3.2))
    for sx in (-1, 1):
        b = b.cut(cq.Workplane("XY").center(sx * RAIL_X, 0).slot2D(RAIL_SLOT[1], RAIL_SLOT[0]).extrude(BAR[2]))
    return b


def mesh(wp):
    path = os.path.join(OUT, "_tmp.stl")
    cq.exporters.export(wp, path)
    m = trimesh.load(path)
    os.remove(path)
    return m


def camera_dummy(i):
    """Red holder in its pocket + clear housing standing out through the wall, for clearance checks."""
    red = cq.Workplane("XY").center(0, CAM_Z).rect(RED[0], RED[1]).extrude(RED[2]).translate((0, 0, CAM_T + 0.05))
    clr = (cq.Workplane("XY").center(0, CAM_Z + CLEAR_DY).rect(CLEARP[0], CLEARP[1]).extrude(CLEARP[2])
           .translate((0, 0, CAM_T + 0.05 - CLEARP[2])))
    return mesh(on_face(i, red)), mesh(on_face(i, clr))


if __name__ == "__main__":
    bm = mesh(body())
    rb = mesh(rail_bar())
    assy = [("body", bm)]
    for sy in (-1, 1):
        b = rb.copy()
        b.apply_translation([0, sy * BAR_Y, -BAR[2]])
        assy.append(("bar", b))
    probs = 0
    for i in range(6):
        red, clr = camera_dummy(i)
        for n, part in (("red holder", red), ("clear housing", clr)):
            for other in (bm,):
                v = trimesh.boolean.intersection([part, other], engine="manifold").volume
                if v > 0.5:
                    print(f"  camera {i} {n} hits a part: {v:.1f} mm3")
                    probs += 1
        assy.append(("camdummy", red))
    agx = trimesh.creation.box(AGX_BOX)
    agx.apply_translation([AGX_C[0], AGX_C[1], FLOOR + AGX_BOX[2] / 2 + 0.5])
    if trimesh.boolean.intersection([agx, bm], engine="manifold").volume > 0.1:
        print("  AGX hits the body")
        probs += 1
    print("clearance problems:", probs)

    for name, m in (("body", bm), ("rail_bar", rb), ("cam_test", mesh(cam_test()))):
        e = m.extents
        print(f"{name:9s} {e[0]:6.1f} x {e[1]:6.1f} x {e[2]:5.1f}  watertight={m.is_watertight}")
        mm = m.copy()
        mm.apply_translation([128 - mm.bounds.mean(0)[0], 128 - mm.bounds.mean(0)[1], -mm.bounds[0][2]])
        mm.export(os.path.join(OUT, name + ".stl"))
    trimesh.util.concatenate([m for n, m in assy if n != "camdummy"]).export(os.path.join(OUT, "assembly.stl"))

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    col = {"body": "#d9a441", "bar": "#333333", "camdummy": "#c0392b"}

    def shade(m, c):
        k = np.clip(m.face_normals @ np.array([-.4, -.5, .8]), 0, 1) * 0.6 + 0.4
        return np.outer(k, matplotlib.colors.to_rgb(c))
    fig = plt.figure(figsize=(16, 7))
    for k, (e, a) in enumerate([(22, -60), (60, 30)]):
        ax = fig.add_subplot(1, 2, k + 1, projection="3d")
        for n, m in assy:
            ax.add_collection3d(Poly3DCollection(m.triangles, facecolors=shade(m, col[n])))
        if k == 1:
            ax.add_collection3d(Poly3DCollection(agx.triangles, facecolors=shade(agx, "#2e8b57")))
        ax.set_xlim(-130, 130); ax.set_ylim(-130, 130); ax.set_zlim(-60, 200)
        ax.view_init(e, a); ax.set_axis_off()
    plt.tight_layout()
    plt.savefig(os.path.join(OUT, "preview.png"), dpi=65)
