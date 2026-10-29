"""SCOUT MINI sensor box, print version: one-piece hexagonal body for the Bambu Lab A1, PLA, open top.

Body: hexagon 240 mm across corners (fits the 256 mm bed), 208 across flats, 130 tall, 2.5 mm walls,
3.2 mm floor, 45 deg fillets at the floor and a 45 deg lip at the top, printed floor-down without supports in one ~8 h job. One camera per face (60 deg apart).
Corner columns inside stiffen the walls and carry pilot holes for a lid later (lidar not decided).
Rail bars are a separate small print.

Camera: Arducam U6251 case (red holder + clear housing), shapes taken from the maker's CAD, ref/U6251.STEP
(Cytron's copy; matches the caliper readings: red 40.12 x 35.12 x 3.5, clear 31.5 x 30.5, M2 holes 34.0 x 29.0).
v10, clean outside: the opening follows the clear housing's rounded outline with an even 0.25 mm gap, the red
holder sits in a pocket that follows its own outline, and the 4 x M2 x 6 go in from inside, through the red
holder's 2.4 mm holes into blind pilots in the wall. No screw heads, recess or seams on the outer face.

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
VERSION = "v11"                  # output folder; bump it for a new version and keep the old ones
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

# camera: Arducam U6251 from its STEP. STEP frame: x across, y from the red holder's back (0) to the clear
# housing's front (14.9), z down. Face-local here: x across, y up, z inwards, red holder's front on the pocket floor.
CAM_STEP = os.path.join(HERE, "ref", "U6251.STEP")
CAM_Z = 92.0
CAM_T = 4.5                     # wall in front of the red holder (v9: 3.0): 6.9 mm of the clear housing shows,
                                # and the M2 screws from inside have 3 mm to bite with 1.5 mm left outside
POCKET_D = 1.0                  # the red holder (3.5 thick) sits this deep in the pad
GAP = 0.25                      # opening round the clear housing, every side
POCKET_GAP = 0.3                # pocket round the red holder, every side
M2_PILOT = (1.7, 3.0)           # M2 self-tapping into PLA: diameter, depth from the pocket floor


def _cam_parts():
    parts = [s.rotate((0, 0, 0), (0, 1, 0), 180).rotate((0, 0, 0), (1, 0, 0), -90).translate((0, CAM_Z, CAM_T + 3.5))
             for s in cq.importers.importStep(CAM_STEP).solids().vals()]
    red = max(parts, key=lambda s: s.BoundingBox().xlen)
    clr = max((s for s in parts if s is not red), key=lambda s: s.BoundingBox().zlen)
    return parts, red, clr


def _section(solid, z):
    """Biggest face of a solid's section at depth z, moved to z = 0."""
    sec = solid.intersect(cq.Face.makePlane(400, 400, basePnt=(0, CAM_Z, z), dir=(0, 0, 1)))
    return max(sec.Faces(), key=lambda f: f.Area()).translate((0, 0, -z))


CAM_PARTS, RED_S, CLEAR_S = _cam_parts()
_red = _section(RED_S, CAM_T + 1.75)            # mid plate
OPENING = cq.Face.makeFromWires(_section(CLEAR_S, CAM_T - 1.6).outerWire().offset2D(GAP)[0])   # just above the ribbon notch
POCKET = cq.Face.makeFromWires(_red.outerWire().offset2D(POCKET_GAP)[0])
M2_HOLES = sorted((round(w.BoundingBox().center.x, 2), round(w.BoundingBox().center.y - CAM_Z, 2))
                  for w in _red.innerWires() if w.BoundingBox().xlen < 3)          # (+-17.0, +-14.5)
M2_CLEAR = 2.4                  # the red holder's holes
_ob, _pb = OPENING.BoundingBox(), POCKET.BoundingBox()
CAM_WIN = (_pb.xlen, _pb.ylen)                  # older names, used by the v5 templates
CAM_CUT = (_ob.xlen, _ob.ylen)
CLEAR_DY = _ob.center.y - CAM_Z
PAD = (CAM_WIN[0] + 8, CAM_WIN[1] + 8, CAM_T + POCKET_D)   # wall thickened round the camera, inside

# vents: low intake, the open top is the exhaust
VENT_W, VENT_H, VENT_PITCH, VENT_Z, VENT_N = 5.0, 24.0, 10.0, 18.0, 0   # v9: no low slots (open top)

# high vents between the camera pads and the top lip: exhaust even with a plate on top
VENT_HI_X, VENT_HI_Z, VENT_HI_H = (), 115.5, 8.0      # v9: replaced by a row of small round holes
VENT_ROW = (0, 9.0, 3.5, 119.5)  # v11: none -- nothing on the outer faces; air comes in through the floor cable holes
                                 # and leaves through the open top (a lid later sits on spacers to keep that gap)
TOP_CHAMFER = 1.0
CABLE_NOTCH = 20.0             # slot below the red holder's pocket for the camera cable
RIBBON = (18.0, 0.8)           # channel for the ribbon, which leaves through a 17.5 x 1.5 notch at the bottom of the clear
                               # housing, right on the red holder: from the opening's lower edge down to the slot

# floor
GRID = 20.0
AGX_C = (0.0, 0.0)              # centred: even cable room all round, holes clear of the rail bars
AGX_SO = [(AGX_C[0] + sx * 45, AGX_C[1] + sy * 45) for sx in (-1, 1) for sy in (-1, 1)]
AGX_BOX = (110.0, 110.0, 72.0)
# v11: AGX cables go down through the floor, one hole each side of the AGX (power one side, LAN/USB the other).
# In the floor, not the walls: a wall hole would leave a sagging bridge, a floor hole prints as plain perimeter.
# x 65..95 keeps 10 mm from the AGX edge (x 55); y -20..20 stays clear of the rail bars (y 55..85).
CABLE_HOLE = (30.0, 40.0, 10.0)  # x size, y size, corner radius
CABLE_X = 80.0

# rail bars. SCOUT MINI OMNI manual V2.1.0, sec. 6.2 p.19: two top rails, 350 long, 16 wide, 230 mm apart
# (centre to centre). T-slot size and bolt not in the manual: the 5.5 slot takes M5; measure the slot on the robot.
RAIL_X = 115.0                  # half rail spacing (manual: 230 / 2)
RAIL_SLOT_C = 115.0             # slot centred on the rail
RAIL_SLOT = (5.5, 10.0)         # +-2.5 mm play for assembly (was 18 long while the pitch was unknown)
BAR = (248.0, 30.0, 8.0)
BAR_Y = 70.0                    # bars run under y 55..85, clear of the AGX holes (y +-45)
BAR_BOLTS_X = (-60.0, -20.0, 20.0, 60.0)   # all inside the 45 deg floor fillet
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
    b = (cq.Workplane("XY").polygon(6, 2 * L).extrude(H).edges("|Z").fillet(FILLET)
         .faces(">Z").edges().chamfer(TOP_CHAMFER))
    inner = cq.Workplane("XY").workplane(offset=FLOOR).polygon(6, 2 * (L - WALL / math.cos(math.radians(30)))).extrude(H)
    b = b.cut(inner)
    ri = L - WALL / math.cos(math.radians(30))          # inner circumradius
    lid_pilots = []
    for k in range(6):                                  # inner corner columns
        a = math.radians(60 * k)
        v = np.array([ri * math.cos(a), ri * math.sin(a)])
        u1 = np.array([math.cos(a + math.radians(120)), math.sin(a + math.radians(120))])
        u2 = np.array([math.cos(a - math.radians(120)), math.sin(a - math.radians(120))])
        pts = [v, v + COL * u1, v + COL * (u1 + u2), v + COL * u2]
        col = cq.Workplane("XY").polyline([tuple(p) for p in pts]).close().extrude(H)
        c = v + COL * (u1 + u2) / 2
        b = b.union(col)
        lid_pilots.append(tuple(c))
    li = ri                                             # inner side length (= inner circumradius)
    for i in range(6):
        # fillet strip at the floor and a lip at the top, both 45 deg so they print without supports
        foot = (cq.Workplane("YZ").polyline([(FLOOR, WALL), (FLOOR, WALL + FOOT), (FLOOR + FOOT, WALL)]).close()
                .extrude(li / 2, both=True))
        lip = (cq.Workplane("YZ").polyline([(H - LIP, WALL), (H, WALL), (H, WALL + LIP)]).close()
               .extrude(li / 2, both=True))
        b = b.union(on_face(i, foot)).union(on_face(i, lip))
    b = b.faces("<Z").edges().chamfer(0.5)              # no elephant foot on the first layer
    # lid pilots go in after the lip, which would otherwise close them over
    b = b.cut(cq.Workplane("XY").workplane(offset=H - 12).pushPoints(lid_pilots).circle(PILOT / 2).extrude(13))
    for i in range(6):
        b = camera_mount(b, lambda wp: on_face(i, wp))
        n, pitch, d, z = VENT_ROW
        holes = [((k - (n - 1) / 2) * pitch, z) for k in range(n)]
        if holes: b = b.cut(on_face(i, cq.Workplane("XY").pushPoints(holes).circle(d / 2).extrude(WALL + 2).translate((0, 0, -1))))
        for x in VENT_HI_X:
            v = (cq.Workplane("XY").center(x, VENT_HI_Z + VENT_HI_H / 2).rect(VENT_W, VENT_HI_H).extrude(WALL + 2)
                 .translate((0, 0, -1)).edges("|Z").fillet(VENT_W / 2 - 0.01))
            b = b.cut(on_face(i, v))
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
    for sx in (-1, 1):
        b = b.cut(cq.Workplane("XY").center(sx * CABLE_X, 0).rect(CABLE_HOLE[0], CABLE_HOLE[1])
                  .extrude(FLOOR).edges("|Z").fillet(CABLE_HOLE[2]))
    bolts = [(x, sy * BAR_Y) for x in BAR_BOLTS_X for sy in (-1, 1)]
    return b.cut(cq.Workplane("XY").pushPoints(bolts).circle(M4 / 2).extrude(FLOOR))


def _prism(face, z0, z1):
    return cq.Workplane("XY").add(cq.Solid.extrudeLinear(face.translate((0, 0, z0)), cq.Vector(0, 0, z1 - z0)))


def camera_mount(b, place):
    """Pad, pocket for the red holder, opening for the clear housing and M2 pilots, in face-local
    coordinates (XY on the outer face, +Z inwards) mapped by `place`."""
    cz = CAM_Z
    pb, ob = POCKET.BoundingBox(), OPENING.BoundingBox()
    b = b.union(place(cq.Workplane("XY").center(0, cz).rect(PAD[0], PAD[1]).extrude(PAD[2])))
    y0, d = cz - PAD[1] / 2, PAD[2] - WALL                # 45 deg slope under the pad instead of a flat ledge
    b = b.union(place(cq.Workplane("YZ").polyline([(y0, WALL), (y0, PAD[2]), (y0 - d, WALL)]).close()
                      .extrude(PAD[0] / 2, both=True)))
    # cable slot from the pocket down through the pad's lower edge
    b = b.cut(place(cq.Workplane("XY").workplane(offset=CAM_T).center(0, pb.ymin - 5)
                    .rect(CABLE_NOTCH, 10).extrude(PAD[2])))
    top = ob.ymin + 0.5                                  # just inside the opening's lower edge
    bot = pb.ymin - 10
    b = b.cut(place(cq.Workplane("XY").workplane(offset=CAM_T - RIBBON[1]).center(0, (top + bot) / 2)
                    .rect(RIBBON[0], top - bot).extrude(RIBBON[1] + 0.01)))
    b = b.cut(place(_prism(POCKET, CAM_T, PAD[2] + 1)))
    b = b.cut(place(_prism(OPENING, -1, PAD[2] + 1)))
    return b.cut(place(cq.Workplane("XY").workplane(offset=CAM_T - M2_PILOT[1])
                       .pushPoints([(x, cz + y) for x, y in M2_HOLES]).circle(M2_PILOT[0] / 2).extrude(M2_PILOT[1] + 0.01)))


def cam_test():
    """The camera mount cut out of a 4 mm wall piece, printed outer face down: fit the camera before the body."""
    w = PAD[0] + 10
    t = cq.Workplane("XY").center(0, CAM_Z).rect(w, PAD[1] + 10).extrude(WALL)
    return camera_mount(t, lambda wp: wp)


def rail_bar():
    b = cq.Workplane("XY").box(*BAR, centered=(True, True, False)).edges("|Z").fillet(4)
    b = b.cut(cq.Workplane("XY").pushPoints([(x, 0) for x in BAR_BOLTS_X]).circle(M4 / 2).extrude(BAR[2]))
    b = b.cut(cq.Workplane("XY").pushPoints([(x, 0) for x in BAR_BOLTS_X]).polygon(6, 8.4).extrude(3.2))   # M4 nut 7.0 across flats; polygon() takes the corner diameter
    for sx in (-1, 1):
        b = b.cut(cq.Workplane("XY").center(sx * RAIL_SLOT_C, 0).slot2D(RAIL_SLOT[1], RAIL_SLOT[0]).extrude(BAR[2]))
    return b


def mesh(wp):
    path = os.path.join(OUT, "_tmp.stl")
    cq.exporters.export(wp, path)
    m = trimesh.load(path)
    os.remove(path)
    return m


def camera_dummy(i):
    """The U6251 solids (red holder, clear housing, tripod insert, board screws) placed on face i."""
    return [on_face(i, cq.Workplane("XY").add(p)).val() for p in CAM_PARTS]


if __name__ == "__main__":
    bw = body()
    bm = mesh(bw)
    rb = mesh(rail_bar())
    assy = [("body", bm)]
    for sy in (-1, 1):
        b = rb.copy()
        b.apply_translation([0, sy * BAR_Y, -BAR[2]])
        assy.append(("bar", b))
    probs = 0
    for i in range(6):
        parts = camera_dummy(i)
        for k, p in enumerate(parts):
            v = bw.val().intersect(p).Volume()          # exact B-rep check against the maker's CAD
            if v > 0.001:
                print(f"  camera {i} part {k} hits the body: {v:.3f} mm3")
                probs += 1
        for k, p in enumerate(parts):
            assy.append(("camred" if p is parts[CAM_PARTS.index(RED_S)] else
                         "camclear" if p is parts[CAM_PARTS.index(CLEAR_S)] else "camsmall", mesh(cq.Workplane().add(p))))
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
    trimesh.util.concatenate([m for n, m in assy if not n.startswith("cam")]).export(os.path.join(OUT, "assembly.stl"))

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    col = {"body": "#d9a441", "bar": "#333333", "camred": "#c0392b", "camclear": "#a9c6e8", "camsmall": "#888888"}

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
