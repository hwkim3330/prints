"""King Crab arm ("킹크랩 팔") for the sensor box lid (lid-v3), Bambu Lab A1, PLA.

Architecture (5 servos, all horn-driven, screws only, every part prints flat without supports):
  J1 base yaw      MG996R  standing in the turret (bolted to lid-v3), turntable on its horn
  J2 shoulder      MG996R  lying in the turntable cradle, upper arm (two side plates) on its horn + M3 idler opposite
  J3 elbow         MG996R  on the upper arm's outer plate, spline inwards, forearm on its horn + M3 idler opposite
  J4 wrist pitch   MG90S   on the forearm's outer plate, spline inwards, the claw's knuckle on its horn + M3 idler
  J5 pincer        MG90S   lying in the claw (propodus); the moving finger (dactylus) on its horn
The claw: a chunky propodus with the fixed finger (pollex), both toothed, the dactylus swinging in a recess
cut into the propodus top so the two rows of teeth meet in one plane.

King-crab styling (Paralithodes), decoration only, every interface as before: spines are 2D blunt triangles in the plate
outlines (they print flat, tips >= 1.6 mm): rows leaning distally along the upper arm (merus) and forearm (carpus),
round the turntable rim, the turret ring and flange, up the cradle plates. Tubercles (blunt cones, 1.8 mm) only on
faces that are up on the bed: Q' outer face, F's face towards Q, the claw's top. The chela: bulbous palm, thick
fixed finger hooking up, arched moving finger with spines on its back and a hooked tip, blunt molar teeth.
lid-v3 (sensor-box/lid.py, ARM=crab) gets the carapace: marginal spines with a rostrum, engraved grooves + tubercles.

Frames: world = lid top centre, z up, the arm reaches +y (camera face 1) at yaw 0. J2..J4 axes run along x.
Servo frame (for both servo types): origin on the spline axis in the plane of the tab undersides, +z = spline
direction, +y from the spline towards the far end of the case.

SERVO AND HORN DIMENSIONS ARE NOT MEASURED: print the fit coupon first (coupon_*.stl) and measure the real servos.

Run:  uv run --with cadquery --with trimesh --with numpy --with scipy --with networkx --with manifold3d \\
        --with rtree --with matplotlib --with shapely python crab-arm/crab.py
"""
import itertools
import math
import os
import sys

import cadquery as cq
import numpy as np
import trimesh
from shapely import affinity
from shapely.geometry import Point, Polygon, box as sbox
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "sensor-box"))

# ---------------------------------------------------------------- servos (guesses: measure the real ones)
# MG996R (TowerPro drawing as sold: 40.7 x 19.7 x 42.9, ears 54, holes 49.5 x 10; heights are typical standard-servo
# values). Horn: the round disc horn from the bag, assumed 21 x 2.5 mm with screw holes on r 7.5.
S = dict(L=40.7, W=19.7, BOT=26.6, TOP=9.9, TAB=2.5, SPAN=54.0, HOLES=(49.5, 10.0), SPL=10.0,
         BOSS=(6.5, 14.9), HORN=17.9, HD=21.0, HT=2.5, HSCREW=[(7.5, a) for a in (0, 90, 180, 270)], PILOT=2.6)
# MG90S (as in ioniq6-testbed chassis.py): 22.8 x 12.2 x 22.7, tab underside 15.9 up, holes 27.8, spline 5.9 from the
# front, horn top 34 above the bottom. Horn: the one-arm horn, assumed hub 7, tip 4, 15 long, 1.6 thick.
M = dict(L=22.8, W=12.2, BOT=15.9, TOP=6.8, TAB=2.5, SPAN=32.2, HOLES=(27.8, 0.0), SPL=5.9,
         BOSS=(5.9, 11.3), HORN=18.1, HD=7.0, HT=1.6, ARM=(15.0, 4.0), HSCREW=[(9.0, 90), (12.0, 90)], PILOT=1.7)
for _s in (S, M):
    _s["HF"] = _s["HORN"] - _s["HT"] + 0.3      # plate face above the tab underside: the horn stands 0.3 proud
    _s["C"] = _s["L"] / 2 - _s["SPL"]           # case centre from the spline, along +y
FIT = 0.25                                       # clearance round servo bodies and horns

PT = 6.0                    # arm side plate thickness (= 14 lines)
PB = 5.0                    # turntable cradle plates
WASH = 1.0                  # washer gap at the idlers
M3C, M3P = 3.4, 2.6         # clearance, self-tapping pilot
H_T = 28.0                  # turret top = J1 tab underside (servo bottom 1.4 above the lid)
R_T = 44.0                  # turret / turntable radius
FLANGE = (100.0, 5.0)       # square, M4 at the corners
BASE_HOLES = [(sx * 40.0, sy * 40.0) for sy in (1, -1) for sx in (-1, 1)]
L1, L2 = 90.0, 80.0        # J2-J3, J3-J4
HINGE = (44.0, 12.0)        # J5 in the claw frame (y, z)
TD = 7.0                    # dactylus thickness

# ---------------------------------------------------------------- the x stack (joint axes run along x)
XA = 9.85                                   # turntable plate A outer face (J2 tab undersides): centres the upper arm
XB = XA - S["BOT"] - 2.0                    # plate B inner face (2 mm behind the J2 case bottom)
Q = (XA + S["HF"], XA + S["HF"] + PT)       # upper arm, horn side (J2 horn inside, J3 servo outside)
QP = (XB - PB - WASH - PT, XB - PB - WASH)  # upper arm, idler side
S3X = Q[1] + S["TAB"]                       # J3 tab undersides (tab tops on Q's outer face, spline -x)
F = (S3X - S["HF"] - PT, S3X - S["HF"])     # forearm, horn side
FP = (QP[1] + WASH, QP[1] + WASH + PT)      # forearm, idler side
S4X = F[1] + M["TAB"]                       # J4 tab undersides (on F's outer face, spline -x)
XK = (FP[1] + WASH, S4X - M["HF"])          # claw knuckle
XG = XK[0] + 1.6 + M["BOT"]                 # J5 tab undersides (servo bottom 1.6 above the claw's bed face)
XD = (XG + M["HF"], XG + M["HF"] + TD)      # dactylus
XT = XD[1]                                  # claw top face
ZU = H_T + S["HF"]                          # turntable disc underside (J1 horn in a pocket there)
ZD = ZU + PT                                # disc top
Z2 = ZD + 18.0                              # J2 axis height above the lid


def rot(axis, deg):
    return trimesh.transformations.rotation_matrix(math.radians(deg), axis)


def tr(*v):
    return trimesh.transformations.translation_matrix(v)


def frame(origin, xs, ys, zs):
    m = np.eye(4)
    m[:3, 0], m[:3, 1], m[:3, 2], m[:3, 3] = xs, ys, zs, origin
    return m


X, Y, Z = np.eye(3)
# servo frames in their mounting part's frame
SF = {
    "j1": frame((0, 0, H_T), -X, -Y, Z),          # turret / world
    "j2": frame((XA, 0, Z2), Z, -Y, X),           # turntable
    "j3": frame((S3X, L1, 0), -Z, -Y, -X),        # upper arm
    "j4": frame((S4X, L2, 0), -Z, -Y, -X),        # forearm
    "j5": frame((XG, HINGE[0], HINGE[1]), Z, -Y, X),   # claw
}


def sp(f, p):
    """servo-frame point -> part frame"""
    return (SF[f] @ np.append(np.asarray(p, float), 1))[:3]


def yz_of(f, x, y):
    p = sp(f, (x, y, 0))
    return (p[1], p[2])


def x_of(f, z):
    return sp(f, (0, 0, z))[0]


# ---------------------------------------------------------------- cadquery helpers
def coords_of(r):
    """polygon ring coordinates without the closing point and without (near) duplicate points (OCC rejects them)"""
    out = []
    for q in list(r.coords)[:-1]:
        if not out or math.dist(q, out[-1]) > 1e-3:
            out.append(q)
    if math.dist(out[0], out[-1]) <= 1e-3:
        out.pop()
    return out


def ext(poly, x0, x1):
    """shapely polygon in (y, z) extruded along x from x0 to x1 (holes cut)."""
    poly = poly.buffer(0)
    polys = list(poly.geoms) if poly.geom_type == "MultiPolygon" else [poly]
    out = None
    for pg in polys:
        s = cq.Workplane("YZ").workplane(offset=x0).polyline(coords_of(pg.exterior)).close().extrude(x1 - x0)
        for h in pg.interiors:
            s = s.cut(cq.Workplane("YZ").workplane(offset=x0 - 1).polyline(coords_of(h)).close().extrude(x1 - x0 + 2))
        out = s if out is None else out.union(s)
    return out


def exz(poly, z0, z1):
    """shapely polygon in (x, y) extruded along z."""
    poly = poly.buffer(0)
    out = None
    for pg in (list(poly.geoms) if poly.geom_type == "MultiPolygon" else [poly]):
        s = cq.Workplane("XY").workplane(offset=z0).polyline(coords_of(pg.exterior)).close().extrude(z1 - z0)
        for h in pg.interiors:
            s = s.cut(cq.Workplane("XY").workplane(offset=z0 - 1).polyline(coords_of(h)).close().extrude(z1 - z0 + 2))
        out = s if out is None else out.union(s)
    return out


def circ(c, r):
    return Point(c).buffer(r, 64)


def hull(*cs):
    return unary_union([circ((y, z), r) for y, z, r in cs]).convex_hull


def spine(p, ang, h, w, tip=1.6, sink=3.0):
    """One king-crab spine on an outline: a blunt triangle standing on point p, pointing at ang (deg), h out of the
    outline, w wide at the outline, a flat tip (>= 1.2 mm so a 0.4 nozzle draws it), sunk `sink` into the plate."""
    a = math.radians(ang)
    d = np.array([math.cos(a), math.sin(a)])
    n = np.array([-d[1], d[0]])
    p = np.asarray(p, float)
    b, t = p - d * sink, p + d * h
    return Polygon([tuple(b - n * w / 2), tuple(b + n * w / 2), tuple(t + n * tip / 2), tuple(t - n * tip / 2)])


def edge_at(poly, y, top=True):
    """The outline point above (top) or below a given y."""
    from shapely.geometry import LineString
    seg = LineString([(y, -500), (y, 500)]).intersection(poly.boundary)
    zs = [g.y for g in getattr(seg, "geoms", [seg])]
    return (y, max(zs) if top else min(zs))


def spine_row(poly, at, top=True, lean=25.0):
    """Spines along the top (or bottom) edge, leaning `lean` deg towards +y (distally, like a crab's leg spines).
    at = [(y, h, w), ...]"""
    return unary_union([spine(edge_at(poly, y, top), (90 - lean) if top else (-90 + lean), h, w) for y, h, w in at])


def knobs(pts, x, up, r=(2.6, 1.0), h=1.8):
    """Tubercles: blunt cones standing on the face x = const, pointing +x (up = 1) or -x, at (y, z) points.
    Only used on faces that are up when printing (they print as small cones on the top surface)."""
    out = None
    for y, z in pts:
        c = cq.Solid.makeCone(r[0], r[1], h + 0.3, cq.Vector(x - 0.3 * up, y, z), cq.Vector(up, 0, 0))
        out = cq.Workplane("XY").add(c) if out is None else out.union(cq.Workplane("XY").add(c))
    return out


def knob_grid(area, pitch, r=2.6):
    """Staggered points inside a shapely area (already shrunk where knobs must not go)."""
    a = area.buffer(-r)
    if a.is_empty:
        return []
    y0, z0, y1, z1 = a.bounds
    dz = pitch * 0.866
    nz, ny = int((z1 - z0) / dz + 1e-6), int((y1 - y0) / pitch + 1e-6)
    z0, y0 = (z0 + z1 - nz * dz) / 2, (y0 + y1 - ny * pitch) / 2      # centred grid
    a = a.buffer(0.05)
    pts = []
    for j in range(nz + 1):
        z = z0 + j * dz
        for y in np.arange(y0 - (pitch / 2 if j % 2 else 0), y1 + pitch, pitch):
            if a.contains(Point(y, z)):
                pts.append((float(y), float(z)))
    return pts


def molars(p0, p1, n, h, up, phase=0.0):
    """Blunt crushing teeth (rounded bumps, king-crab molars) along p0 -> p1, to the left (up=1) or right (up=-1)."""
    p0, p1 = np.array(p0, float), np.array(p1, float)
    d = p1 - p0
    nrm = np.array([-d[1], d[0]]) / np.linalg.norm(d) * up
    pts = [tuple(p0)]
    for k in range(n):
        a, b = (k + phase) / n, (k + phase + 1) / n
        for t in np.linspace(0, math.pi, 9):
            s = a + (b - a) * (1 - math.cos(t)) / 2
            pts.append(tuple(p0 + d * s + nrm * h * math.sin(t) ** 0.7))
    pts.append(tuple(p1))
    return pts


def servo_cuts(part, f, kind, plate, through=True):
    """Window for the case and tab pilots, in a plate spanning x in `plate`, for servo f mounted on it."""
    s = S if kind == "S" else M
    c0 = yz_of(f, -s["W"] / 2 - FIT, -s["SPL"] - FIT)
    c1 = yz_of(f, s["W"] / 2 + FIT, s["L"] - s["SPL"] + FIT)
    win = sbox(min(c0[0], c1[0]), min(c0[1], c1[1]), max(c0[0], c1[0]), max(c0[1], c1[1]))
    part = part.cut(ext(win, plate[0] - 1, plate[1] + 1))
    hx, hy = s["HOLES"]
    holes = [yz_of(f, sx * hy / 2, s["C"] + sy * hx / 2) for sx in ((-1, 1) if hy else (0,)) for sy in (-1, 1)]
    return part.cut(ext(unary_union([circ(h, s["PILOT"] / 2) for h in holes]), plate[0] - 1, plate[1] + 1))


def horn_outline(f, kind, grow=FIT):
    s = S if kind == "S" else M
    if kind == "S":
        return circ(yz_of(f, 0, 0), s["HD"] / 2 + grow)
    a, tipr = s["ARM"]
    return unary_union([circ(yz_of(f, 0, 0), s["HD"] / 2 + grow), circ(yz_of(f, 0, -a), tipr / 2 + grow)]).convex_hull


def horn_cuts(part, f, kind, plate, skip=lambda yz: False, screw_d=2.4, centre=7.0, centre_depth=None):
    """Pocket for the horn on the plate face towards the servo, screw holes through, a hole for the centre screw."""
    s = S if kind == "S" else M
    a, b = sorted((x_of(f, s["HORN"]), x_of(f, s["HF"] - 0.3 - 1)))      # pocket floor .. past the plate face
    part = part.cut(ext(horn_outline(f, kind), a, b))
    pts = [yz_of(f, r * math.cos(math.radians(t)), -r * math.sin(math.radians(t))) for r, t in s["HSCREW"]]
    pts = [p for p in pts if not skip(p)]
    if pts:
        part = part.cut(ext(unary_union([circ(p, screw_d / 2) for p in pts]), plate[0] - 1, plate[1] + 1))
    if centre_depth is None:
        lo, hi = plate[0] - 1, plate[1] + 1
    else:                                       # blind recess for the centre screw head, from the pocket floor
        fl = x_of(f, s["HORN"])
        lo, hi = (fl - centre_depth, fl + 0.1) if x_of(f, s["HORN"] + 1) < fl else (fl - 0.1, fl + centre_depth)
    return part.cut(ext(circ(yz_of(f, 0, 0), centre / 2), lo, hi)), pts


# ---------------------------------------------------------------- parts
def turret():
    """Fixed base on the lid: square flange (4 x M4 to lid-v3), J1 servo standing in a box, thrust ring on top."""
    fl = sbox(-FLANGE[0] / 2, -FLANGE[0] / 2, FLANGE[0] / 2, FLANGE[0] / 2)
    fl = Polygon(fl.buffer(-6).buffer(6, 16).exterior)
    # king-crab look: spines on the flange's left, right and front edges (the back edge stays straight: the lid's cable
    # slot is right behind it), and low ridges round the ring
    fs = [spine((sx * FLANGE[0] / 2, y), 90 - sx * 90, h, 11) for sx in (-1, 1) for y, h in ((-24, 6), (0, 8), (24, 6))]
    fs += [spine((x, FLANGE[0] / 2), 90, h, 11) for x, h in ((-24, 6), (0, 8), (24, 6))]
    t = exz(unary_union([fl] + fs), 0, FLANGE[1])
    ring = circ((0, 0), R_T).difference(circ((0, 0), R_T - 3.0))
    t = t.union(exz(unary_union([spine((R_T * math.cos(a), R_T * math.sin(a)), math.degrees(a), 4.0, 7)
                                 for a in np.radians(np.arange(0, 360, 45) + 22.5)]).difference(circ((0, 0), R_T - 3.0)),
                    0, 14))   # low buttress ridges round the ring (full-height ridges cost 45 min of print time)
    t = t.union(exz(ring, 0, ZU - 0.5))         # 0.5 under the turntable: it takes the arm's tipping load
    c = -S["C"]                                 # case centre y (Y_s = -y)
    blk = sbox(-S["W"] / 2 - 4.5, c - S["SPAN"] / 2 - 4.5, S["W"] / 2 + 4.5, c + S["SPAN"] / 2 + 4.5)
    t = t.union(exz(blk.intersection(circ((0, 0), R_T - 0.5)), 0, H_T))
    for a in (0, 90, 180, 270):                 # ribs from the box to the ring
        rib = affinity.rotate(sbox(0, -1.5, R_T - 1.5, 1.5), a, origin=(0, 0))
        t = t.union(exz(rib, 0, H_T - 6))
    win = sbox(-S["W"] / 2 - FIT, -(S["L"] - S["SPL"]) - FIT, S["W"] / 2 + FIT, S["SPL"] + FIT)
    t = t.cut(exz(win, -1, H_T + 1))
    hx, hy = S["HOLES"]
    t = t.cut(cq.Workplane("XY").workplane(offset=H_T - 12).pushPoints(
        [(sx * hy / 2, c + sy * hx / 2) for sx in (-1, 1) for sy in (-1, 1)]).circle(M3P / 2).extrude(13))
    t = t.cut(cq.Workplane("XY").pushPoints(BASE_HOLES).circle(4.5 / 2).extrude(FLANGE[1] + 1))
    return t   # the J1 lead goes straight down through lid-v3's hole under the slot


def turntable():
    """Disc on the J1 horn with the shoulder cradle: plate A holds the J2 servo by its ears (open notch from the top),
    plate B takes the idler screw."""
    t = exz(unary_union([circ((0, 0), R_T)] + [spine((R_T * math.cos(a), R_T * math.sin(a)), math.degrees(a), 4.0, 8)
                                              for a in np.radians(np.arange(0, 360, 20))]), ZU, ZD)   # spiny rim
    # J1 horn pocket in the disc underside. Its screws go in from the top: skip the holes under the plates
    a, b = ZU - 1, H_T + S["HORN"]
    t = t.cut(exz(circ((0, 0), S["HD"] / 2 + FIT), a, b))
    pts = [sp("j1", (r * math.cos(math.radians(q)), r * math.sin(math.radians(q)), 0))[:2] for r, q in S["HSCREW"]]
    under = lambda x: XA - PB - 2.5 < x < XA + 2.5 or XB - PB - 2.5 < x < XB + 2.5
    pts = [p for p in pts if not under(p[0])]
    print(f"  J1 horn screws from the top: {len(pts)} of {len(S['HSCREW'])} (the others are under the cradle plates)")
    t = t.cut(cq.Workplane("XY").pushPoints([tuple(p) for p in pts]).circle(1.2).extrude(ZD + 1))
    t = t.cut(exz(circ((0, 0), 3.5), ZU - 1, ZD + 1))
    c = S["C"]
    prof = sbox(-42, ZD - 0.01, 22, Z2 + 14).buffer(-3).buffer(3, 16)
    prof = unary_union([prof, sbox(-42, ZD - 0.01, 22, ZD + 5)])
    # spines up the cradle plates' top edges (they print standing, the spines point up: no overhang). The upper arm's
    # spacers sweep r 24..40 round J2 over the shoulder range, so the spines stay outside that (back) or under r 23
    top = Z2 + 14
    sa = spine((-36, top), 105, 7, 9)
    sb = unary_union([sa, spine((-13, top), 90, 4.5, 8)])
    t = t.union(ext(unary_union([prof, sa]), XA - PB, XA))     # plate A (5 thick)
    t = t.union(ext(unary_union([prof, sb]), XB - PB, XB))     # plate B
    t = t.union(ext(sbox(-42, ZD - 0.01, -37, ZD + 14), XB - PB, XA))     # back wall ties A and B
    # notch for the J2 case, open at the top
    t = t.cut(ext(sbox(-(S["L"] - S["SPL"]) - FIT, Z2 - S["W"] / 2 - FIT, S["SPL"] + FIT, Z2 + 40), XA - PT, XA + 1))
    hx, hy = S["HOLES"]
    t = t.cut(ext(unary_union([circ((-(c + sy * hx / 2), Z2 + sx * hy / 2), M3P / 2) for sx in (-1, 1) for sy in (-1, 1)]),
                  XA - 6, XA + 1))
    t = t.cut(ext(circ((0, Z2), M3P / 2), XB - PT - 1, XB + 1))    # J2 idler pilot
    t = t.cut(ext(sbox(-36, ZD - 1, -31, ZD + 8), XB - PT, XA + 1))  # J2 lead out the back
    return t


def upper_plate_outline():
    """The merus: a long spiny leg segment, a row of big spines along the top edge, smaller ones underneath."""
    o = hull((0, 0, 16), (L1, 0, 21))
    return unary_union([o, spine_row(o, [(22, 6, 9), (35, 8, 10), (48, 9, 10), (61, 8, 10), (73, 6, 9)]),
                        spine_row(o, [(30, 4, 8), (46, 5, 8), (62, 4, 8)], top=False)])


def upper_knobs():
    """Tubercles on Q' outer face (-x, up on the bed): staggered pairs along the plate, clear of the screw heads."""
    keep = hull((0, 0, 13), (L1, 0, 17)).difference(unary_union(
        [circ((0, 0), 12), circ((L1, 0), 12)] + [circ(c, 6.5) for c in SPACERS_U]))
    return knob_grid(keep, 9.0)


def upper_arm_q():
    p = ext(upper_plate_outline(), *Q)
    p, pts = horn_cuts(p, "j2_u", "S", Q)
    p = servo_cuts(p, "j3", "S", Q)
    return p.cut(ext(unary_union([circ(c, M3C / 2) for c in SPACERS_U]), Q[0] - 1, Q[1] + 1))


def upper_arm_qp():
    p = ext(upper_plate_outline(), *QP)
    p = p.union(knobs(upper_knobs(), QP[0], -1))
    p = p.cut(ext(unary_union([circ((0, 0), M3C / 2), circ((L1, 0), M3C / 2)] + [circ(c, M3C / 2) for c in SPACERS_U]),
                  QP[0] - 1, QP[1] + 1))
    return p


def fore_plate_outline():
    """The carpus: spines along the top; underneath only beyond the upper arm's spacer when folded."""
    o = hull((0, 0, 15), (L2, 0, 13))
    return unary_union([o, spine_row(o, [(22, 6, 9), (35, 7, 10), (48, 7, 10), (60, 5, 8)]),
                        spine_row(o, [(50, 4, 8), (63, 3.5, 7)], top=False)])


def fore_knobs():
    """Tubercles on F's +x face (up on the bed), between the J3 horn and the J4 servo ears, off the spacer screws."""
    keep = hull((0, 0, 12), (L2, 0, 10)).intersection(sbox(16, -20, 56, 20)).difference(
        unary_union([circ(c, 6.5) for c in SPACERS_F]))
    return knob_grid(keep, 8.5, r=2.4)


def forearm_f():
    p = ext(fore_plate_outline(), *F).union(knobs(fore_knobs(), F[1], 1, r=(2.4, 0.9), h=1.6))
    p, _ = horn_cuts(p, "j3_f", "S", F)
    p = servo_cuts(p, "j4", "M", F)
    return p.cut(ext(unary_union([circ(c, M3C / 2) for c in SPACERS_F]), F[0] - 1, F[1] + 1))


def forearm_fp():
    p = ext(fore_plate_outline(), *FP)
    return p.cut(ext(unary_union([circ((0, 0), M3P / 2), circ((L2, 0), M3C / 2)] + [circ(c, M3C / 2) for c in SPACERS_F]),
                     FP[0] - 1, FP[1] + 1))


SPACERS_U = [(32.0, 0.0), (50.0, 0.0)]
SPACERS_F = [(30.0, 0.0), (48.0, 0.0)]
SPACER = 11.0


def spacer(span):
    s = cq.Workplane("XY").rect(SPACER, SPACER).extrude(span).edges("|Z").chamfer(1.5)
    s = s.cut(cq.Workplane("XY").circle(M3P / 2).extrude(12)).cut(cq.Workplane("XY").workplane(offset=span - 12).circle(M3P / 2).extrude(13))
    return s


def spacer_in(frame_x, c):
    """A spacer placed between plates (x from frame_x[0] to frame_x[1]) at (y, z) = c, in the link frame."""
    s = spacer(frame_x[1] - frame_x[0])
    return s.rotate((0, 0, 0), (0, 1, 0), 90).translate((frame_x[0], c[0], c[1]))


# claw profile (claw frame: origin on J4, y forward, z up at q4 = 0)
POLLEX_EDGE = ((62.0, 0.0), (104.0, -5.0))
DACT_EDGE = ((102.0, 2.0), (60.0, 7.0))


def palm_base():
    """The king crab's heavy chela: a bulbous palm (manus) and a thick fixed finger curving up at the tip."""
    palm = hull((27, -14, 9.5), (27, 15, 10.5), (60, -16, 10), (58, 17, 9.5))
    pollex = Polygon([(48, -25), (64, -25.5), (80, -23.5), (94, -18.5), (104, -12.5), (110, -6.5), (111.5, -2.5),
                      (109, -1.5), (106, -3.5)] + molars(POLLEX_EDGE[1], POLLEX_EDGE[0], 5, 2.6, -1) + [(52, 2)])
    return unary_union([palm, pollex])


def palm_outline():
    """the palm with spines: a row on the upper margin behind the moving finger, a row under the palm and the finger"""
    b = palm_base()
    sp = [spine_row(b, [(25, 6, 9), (35, 7, 9)], lean=-15),                        # upper margin, behind the dactylus
          spine_row(b, [(34, 5, 9), (47, 6, 10), (60, 6, 10), (74, 5, 9), (88, 4, 8)], top=False, lean=30)]
    return unary_union([b] + sp)


def dactyl_outline():
    """closed, in the claw frame: the moving finger, arched, spines on its back, hooked tip, blunt molars"""
    pts = [(44, 22), (58, 27.5), (74, 27.5), (90, 22.5), (102, 14.5), (110, 6.5), (113, 2.5), (112, -0.5), (108, -1)] \
        + molars(DACT_EDGE[0], DACT_EDGE[1], 5, 2.6, 1, 0.5) + [(50, 4), (44, 2)]
    d = Polygon(pts).buffer(0)
    return unary_union([d, circ(HINGE, 10), spine_row(d, [(62, 4.5, 8), (76, 4.5, 8), (89, 4, 7)], lean=35)])


def knuckle_outline():
    return unary_union([circ((0, 0), 12.5), sbox(0, -12.5, 24, 12.5)])


def claw():
    k = ext(knuckle_outline(), XK[0], XK[1])
    c = k.union(ext(palm_outline(), XK[0], XT))
    # J4 horn in the knuckle's +x face; its screws from the bed side through counterbores
    c, pts = horn_cuts(c, "j4_c", "M", XK, centre=5.0, centre_depth=3.0, screw_d=2.2)
    fl = x_of("j4_c", M["HORN"])
    c = c.cut(ext(unary_union([circ(p, 2.4) for p in pts]), XK[0] - 1, fl - 6))    # heads: M2 x 8 reach the horn
    c = c.cut(ext(circ((0, 0), M3P / 2), XK[0] - 1, XK[0] + 10))                  # J4 idler pilot
    # J5 servo: ears pocket from the top down to the ledge, case pocket below, pilots in the ledge
    s = M
    yc = HINGE[0] - s["C"]
    c = c.cut(ext(sbox(yc - s["SPAN"] / 2 - FIT, HINGE[1] - s["W"] / 2 - FIT, yc + s["SPAN"] / 2 + FIT, HINGE[1] + s["W"] / 2 + FIT), XG, XT + 1))
    c = c.cut(ext(sbox(HINGE[0] - (s["L"] - s["SPL"]) - FIT, HINGE[1] - s["W"] / 2 - FIT, HINGE[0] + s["SPL"] + FIT,
                       HINGE[1] + s["W"] / 2 + FIT), XG - s["BOT"] - 0.3, XT + 1))
    c = c.cut(ext(unary_union([circ((yc + sy * s["HOLES"][0] / 2, HINGE[1]), s["PILOT"] / 2) for sy in (-1, 1)]), XG - 8, XG + 0.1))
    # lead: from the back of the case pocket out through the palm's back face, open at the top
    c = c.cut(ext(sbox(10, HINGE[1] - 3.5, HINGE[0] - (s["L"] - s["SPL"]), HINGE[1] + 3.5), XG - s["BOT"] + 2, XT + 1))
    # recess the dactylus swings in (0..45 deg open), 0.8 mm all round
    sweep = unary_union([affinity.rotate(dactyl_outline(), a, origin=HINGE) for a in range(0, 46, 3)]).buffer(0.8)
    c = c.cut(ext(sweep, XD[0] - 1.0, XT + 1))
    # tubercles on the top face (it is up on the bed), wherever the top is solid
    c = c.union(knobs(claw_knobs(), XT, 1))
    return c


def claw_knobs():
    s = M
    yc = HINGE[0] - s["C"]
    open_top = unary_union([
        sbox(yc - s["SPAN"] / 2 - FIT, HINGE[1] - s["W"] / 2 - FIT, yc + s["SPAN"] / 2 + FIT, HINGE[1] + s["W"] / 2 + FIT),
        sbox(10, HINGE[1] - 3.5, HINGE[0], HINGE[1] + 3.5),
        unary_union([affinity.rotate(dactyl_outline(), a, origin=HINGE) for a in range(0, 46, 3)]).buffer(0.8)])
    return knob_grid(palm_base().buffer(-1.0).difference(open_top.buffer(1.5)), 8.0)


def dactyl():
    """moving finger, in the claw frame (closed); horn pocket on its -x face, screws from the +x face"""
    d = ext(dactyl_outline(), *XD)
    d, _ = horn_cuts(d, "j5", "M", XD, centre=5.0, screw_d=2.2)
    return d


# ---------------------------------------------------------------- servo frames for the horn side of each joint
# (the horn turns with the driven part, so its frame there is the servo frame at the joint's zero)
SF["j2_u"] = tr(0, 0, -Z2) @ SF["j2"]       # in the upper arm frame (origin on J2)
SF["j3_f"] = tr(0, -L1, 0) @ SF["j3"]       # in the forearm frame (origin on J3)
SF["j4_c"] = tr(0, -L2, 0) @ SF["j4"]       # in the claw frame (origin on J4)


def coupon():
    """Fit test, ~20 min, one flat 3 mm plate: frames that hold one MG996R and one MG90S by their ears (case through the
    window, M3 / M2 self-tapping into the pilots), and the two horn pockets as the arm has them (depth = horn - 0.3,
    screw holes, centre hole). Drop each horn in: it must sit flat, its holes over ours, 0.3 mm proud."""
    T0 = 3.0
    xs, xm = -40.0, 26.0                        # spline positions; cases run +x
    pads = [sbox(xs + S["C"] - S["SPAN"] / 2 - 4, -S["W"] / 2 - 7, xs + S["C"] + S["SPAN"] / 2 + 4, S["W"] / 2 + 7),
            sbox(xm + M["C"] - M["SPAN"] / 2 - 3, -M["W"] / 2 - 6, xm + M["C"] + M["SPAN"] / 2 + 3, M["W"] / 2 + 6),
            sbox(-30, S["W"] / 2 + 5, -2, S["W"] / 2 + 34),          # disc horn pad
            sbox(4, M["W"] / 2 + 4, 40, M["W"] / 2 + 20)]            # arm horn pad
    base = exz(unary_union(pads).buffer(-2).buffer(2), 0, T0)
    cut = [sbox(xs - S["SPL"] - FIT, -S["W"] / 2 - FIT, xs + S["L"] - S["SPL"] + FIT, S["W"] / 2 + FIT),
           sbox(xm - M["SPL"] - FIT, -M["W"] / 2 - FIT, xm + M["L"] - M["SPL"] + FIT, M["W"] / 2 + FIT)]
    base = base.cut(exz(unary_union(cut), -1, T0 + 1))
    pil = [(xs + S["C"] + sx * S["HOLES"][0] / 2, sy * S["HOLES"][1] / 2) for sx in (-1, 1) for sy in (-1, 1)]
    base = base.cut(cq.Workplane("XY").pushPoints(pil).circle(S["PILOT"] / 2).extrude(T0 + 1))
    base = base.cut(cq.Workplane("XY").pushPoints([(xm + M["C"] + sx * M["HOLES"][0] / 2, 0) for sx in (-1, 1)])
                    .circle(M["PILOT"] / 2).extrude(T0 + 1))
    dc = (-16.0, S["W"] / 2 + 19.5)
    ac = (30.0, M["W"] / 2 + 12)               # hub centre; the arm points -x
    disc = circ(dc, S["HD"] / 2 + FIT)
    arm = unary_union([circ(ac, M["HD"] / 2 + FIT), circ((ac[0] - M["ARM"][0], ac[1]), M["ARM"][1] / 2 + FIT)]).convex_hull
    base = base.cut(exz(disc, T0 - (S["HT"] - 0.3), T0 + 1)).cut(exz(arm, T0 - (M["HT"] - 0.3), T0 + 1))
    holes = [(dc[0] + r * math.cos(math.radians(t)), dc[1] + r * math.sin(math.radians(t)), 1.2) for r, t in S["HSCREW"]]
    holes += [(ac[0] - r, ac[1], 1.1) for r, t in M["HSCREW"]] + [(dc[0], dc[1], 3.5), (ac[0], ac[1], 2.5)]
    for x, y, r in holes:
        base = base.cut(cq.Workplane("XY").center(x, y).circle(r).extrude(T0 + 1))
    return base


# ---------------------------------------------------------------- meshes, kinematics, checks
def mesh(wp):
    import box
    return box.mesh(wp)


def servo_dummy(kind):
    """case, ears, boss, horn: trimesh solids in the servo frame"""
    s = S if kind == "S" else M
    body = trimesh.creation.box((s["W"], s["L"], s["BOT"] + s["TOP"]))
    body.apply_translation((0, s["C"], (s["TOP"] - s["BOT"]) / 2))
    ears = trimesh.creation.box((s["W"], s["SPAN"], s["TAB"]))
    ears.apply_translation((0, s["C"], s["TAB"] / 2))
    boss = trimesh.creation.cylinder(s["BOSS"][0], s["BOSS"][1] - s["TOP"], sections=48)
    boss.apply_translation((0, 0, (s["BOSS"][1] + s["TOP"]) / 2))
    spl = trimesh.creation.cylinder(2.4, s["HORN"] - s["HT"] - s["BOSS"][1], sections=24)
    spl.apply_translation((0, 0, (s["HORN"] - s["HT"] + s["BOSS"][1]) / 2))
    if kind == "S":
        horn = trimesh.creation.cylinder(s["HD"] / 2, s["HT"], sections=64)
    else:
        a, tipr = s["ARM"]
        pts = [(math.cos(t) * s["HD"] / 2, math.sin(t) * s["HD"] / 2) for t in np.linspace(0, 2 * math.pi, 32)] + \
              [(math.cos(t) * tipr / 2, -a + math.sin(t) * tipr / 2) for t in np.linspace(0, 2 * math.pi, 32)]
        horn = trimesh.convex.convex_hull([(x, y, z) for x, y in pts for z in (-s["HT"] / 2, s["HT"] / 2)])
    horn.apply_translation((0, 0, s["HORN"] - s["HT"] / 2))
    return trimesh.boolean.union([body, ears, boss, spl], engine="manifold"), horn


def build():
    parts = {}
    parts["turret"] = (turret(), "W")
    parts["turntable"] = (turntable(), "T")
    parts["upper_q"] = (upper_arm_q(), "U")
    parts["upper_qp"] = (upper_arm_qp(), "U")
    for i, c in enumerate(SPACERS_U):
        parts[f"spacer_u{i}"] = (spacer_in((QP[1], Q[0]), c), "U")
    parts["fore_f"] = (forearm_f(), "F")
    parts["fore_fp"] = (forearm_fp(), "F")
    for i, c in enumerate(SPACERS_F):
        parts[f"spacer_f{i}"] = (spacer_in((FP[1], F[0]), c), "F")
    parts["claw"] = (claw(), "C")
    parts["dactyl"] = (dactyl(), "D")
    return parts


def chain(q):
    """frame -> world transforms for joint angles q = (yaw, shoulder, elbow, wrist, pincer) in degrees"""
    q1, q2, q3, q4, q5 = q
    T = rot(Z, q1)
    U = T @ tr(0, 0, Z2) @ rot(X, q2)
    Fm = U @ tr(0, L1, 0) @ rot(X, q3)
    C = Fm @ tr(0, L2, 0) @ rot(X, q4)
    D = C @ tr(0, *HINGE) @ rot(X, q5) @ tr(0, -HINGE[0], -HINGE[1])
    return {"W": np.eye(4), "T": T, "U": U, "F": Fm, "C": C, "D": D}


# servo dummies: (name, servo frame, mounted on, horn turns with)
SERVOS = [("j1", "S", "W", "T", SF["j1"]), ("j2", "S", "T", "U", SF["j2"]), ("j3", "S", "U", "F", SF["j3"]),
          ("j4", "M", "F", "C", SF["j4"]), ("j5", "M", "C", "D", SF["j5"])]
# the horn sits at the joint: in the driven frame it is the servo frame moved to that frame's origin
HORN_IN = {"j1": SF["j1"], "j2": SF["j2_u"], "j3": SF["j3_f"], "j4": SF["j4_c"],
           "j5": tr(0, *HINGE) @ tr(0, -HINGE[0], -HINGE[1]) @ SF["j5"]}

TIP = (108.0, -6.0)     # the fixed finger's tip in the claw frame


def ik(y, z, claw_deg, yaw=0.0, pincer=0.0):
    """Joint angles that put the fixed finger's tip at (y, z) (world, in the arm's plane) with the claw pointing at
    claw_deg (absolute, 0 = forward, -90 = down). Elbow up."""
    a = math.radians(claw_deg)
    wy = y - (TIP[0] * math.cos(a) - TIP[1] * math.sin(a))
    wz = z - (TIP[0] * math.sin(a) + TIP[1] * math.cos(a)) - Z2
    c3 = (wy * wy + wz * wz - L1 * L1 - L2 * L2) / (2 * L1 * L2)
    q3 = -math.acos(max(-1.0, min(1.0, c3)))
    q2 = math.atan2(wz, wy) - math.atan2(L2 * math.sin(q3), L1 + L2 * math.cos(q3))
    q2, q3 = math.degrees(q2), math.degrees(q3)
    return (yaw, round(q2, 1), round(q3, 1), round(claw_deg - q2 - q3, 1), pincer)


POSES = {  # yaw, shoulder (0 = upper arm forward, 90 = up), elbow (rel.), wrist (rel.), pincer (0 closed .. 45 open)
    "home (upright, forearm forward)": (0, 90, -90, 0, 0),
    "reach forward": (0, 20, -15, 0, 40),
    "pick on the lid, claw down": ik(85, 4, -90, pincer=45),
    "over the front edge, down": ik(150, -30, -75, pincer=30),
    "tucked": (0, 115, -145, 50, 0),
    "low to the side": (90, 15, -40, -40, 20),
    "high, claw up": (-60, 100, -20, 80, 45),
}


if __name__ == "__main__":
    os.environ["ARM"] = "crab"
    import box
    import lid as lidmod

    print(f"x stack: A {XA:.2f}  B {XB:.2f}  Q {Q}  Q' {QP}  F {F}  F' {FP}  knuckle {XK}  J5 ears {XG:.2f}  dactyl {XD}")
    print(f"J1 tab plane z {H_T}, disc {ZU:.1f}..{ZD:.1f}, J2 axis z {Z2:.1f}")
    parts = build()
    meshes = {}
    for n, (wp, fr) in parts.items():
        m = mesh(wp)
        meshes[n] = (m, fr)
        print(f"{n:11s} {m.extents.round(1)}  watertight={m.is_watertight}  {m.volume / 1000:6.1f} cm3")
    dummies = {}
    for n, kind, on, drv, sfm in SERVOS:
        body, horn = servo_dummy(kind)
        b = body.copy(); b.apply_transform(sfm)
        h = horn.copy(); h.apply_transform(HORN_IN[n])
        dummies[n + "_case"] = (b, on)
        dummies[n + "_horn"] = (h, drv)
    lm = mesh(lidmod.lid())
    lm.apply_translation((0, 0, -(lidmod.GAP + lidmod.T)))
    fixed = {"lid": (lm, "W")}

    allm = {**meshes, **dummies, **fixed}
    # designed contacts: the horn in its pocket, a case in its own mount (exact fit), the ears on their plate
    allowed = {("j1_case", "turret"), ("j1_horn", "turntable"), ("j2_case", "turntable"), ("j2_horn", "upper_q"),
               ("j3_case", "upper_q"), ("j3_horn", "fore_f"), ("j4_case", "fore_f"), ("j4_horn", "claw"),
               ("j5_case", "claw"), ("j5_horn", "dactyl"), ("j1_case", "j1_horn"), ("j2_case", "j2_horn"),
               ("j3_case", "j3_horn"), ("j4_case", "j4_horn"), ("j5_case", "j5_horn"), ("turret", "lid")}
    for n, (m, fr) in allm.items():
        if not m.is_volume:
            print("  not a volume:", n, m.is_watertight, m.volume)
            m.merge_vertices(); m.fix_normals()
    probs = 0
    for pname, q in POSES.items():
        ch = chain(q)
        world = {}
        for n, (m, fr) in allm.items():
            w = m.copy(); w.apply_transform(ch[fr]); world[n] = w
        bad = []
        for a, b in itertools.combinations(world, 2):
            ma, mb = world[a], world[b]
            if (ma.bounds[0] > mb.bounds[1]).any() or (mb.bounds[0] > ma.bounds[1]).any():
                continue
            v = trimesh.boolean.intersection([ma, mb], engine="manifold").volume
            lim = 0.5 if ((a, b) in allowed or (b, a) in allowed) else 0.05
            if v > lim:
                bad.append(f"{a}/{b} {v:.1f} mm3")
        tip = (ch["C"] @ np.array([0, *TIP, 1]))[:3]
        print(f"pose {pname:34s} q={q}  claw tip at {tip.round(0)}  " + ("OK" if not bad else "HITS: " + ", ".join(bad)))
        probs += len(bad)
    # the claw's tip must stay above the lid in the reach pose, and the turret on the lid's bolt circle
    print("collision problems:", probs)

    # ------------------------------------------------------------ torque check (arm straight out, worst case)
    PLA = 1.24e-3                   # g/mm3
    FILL = {"claw": 0.36}           # sliced grams / solid grams (3 walls, 15 % infill), from the slicer runs

    ch = chain((0, 0, 0, 0, 0))
    LEVEL = {"U": 2, "F": 3, "C": 4, "D": 4}      # first joint that does NOT carry it
    load = []                                     # (grams, world y, level)
    for n, (m, fr) in meshes.items():
        if fr in LEVEL:
            load.append((m.volume * PLA * FILL.get(n, 0.48), (ch[fr] @ np.append(m.center_mass, 1))[1], LEVEL[fr]))
    for n, g, lv, y in (("j3", 55 + 3, 3, L1), ("j4", 13.4 + 1, 4, L1 + L2), ("j5", 13.4 + 1, 5, L1 + L2 + HINGE[0] - M["C"])):
        load.append((g, y, lv))
    load += [(12, L1 / 2, 2), (8, L1 + L2 / 2, 3), (5, L1 + L2 + 40, 4)]           # screws, spacers' screws, leads
    load.append((50, L1 + L2 + 85, 5))                                             # payload in the claw
    total = sum(g for g, y, lv in load)

    def torque(j, axis_y):
        return sum(g * (y - axis_y) for g, y, lv in load if lv >= j) / 1e4     # g mm -> kg cm
    t2, t3, t4 = torque(2, 0), torque(3, L1), torque(4, L1 + L2)
    print(f"moving mass {total:.0f} g (incl. 50 g payload), arm straight out horizontally")
    for n, t, lim in (("J2 shoulder (MG996R)", t2, 9.0), ("J3 elbow (MG996R)", t3, 9.0), ("J4 wrist (MG90S)", t4, 1.8)):
        print(f"  {n:22s} {t:4.2f} kg cm of {lim} stall = {t / lim:.0%}")
    TORQUE = (t2, t3, t4, total)

    # ------------------------------------------------------------ export for printing
    def lay(m, rx=0.0, ry=0.0):
        m = m.copy()
        if rx: m.apply_transform(rot(X, rx))
        if ry: m.apply_transform(rot(Y, ry))
        m.apply_translation([128 - m.bounds.mean(0)[0], 128 - m.bounds.mean(0)[1], -m.bounds[0][2]])
        return m
    orient = {"turret": (0, 0), "turntable": (0, 0), "upper_q": (0, 90), "upper_qp": (0, 90),
              "fore_f": (0, -90), "fore_fp": (0, 90), "claw": (0, -90), "dactyl": (0, 90)}
    # upper_q: pocket on its -x face -> -x face up (ry = +90 puts +x down); fore_f: pocket on +x -> +x up
    out = {}
    for n, (m, fr) in meshes.items():
        if n.startswith("spacer"):
            continue
        out[n] = lay(m, *[0, orient[n][1]])
        out[n].export(os.path.join(HERE, n + ".stl"))
    sp_u = lay(mesh(spacer(Q[0] - QP[1])), 0, 90)      # lying on a side: full face on the bed
    sp_f = lay(mesh(spacer(F[0] - FP[1])), 0, 90)
    sp_u.export(os.path.join(HERE, "spacer_upper.stl"))
    sp_f.export(os.path.join(HERE, "spacer_fore.stl"))
    lay(mesh(coupon())).export(os.path.join(HERE, "coupon.stl"))
    for n in list(out) + ["spacer_upper", "spacer_fore", "coupon"]:
        m = trimesh.load(os.path.join(HERE, n + ".stl"))
        flat = m.area_faces[(m.face_normals[:, 2] < -0.999) & (m.triangles_center[:, 2] < 0.01)].sum()
        print(f"print {n:13s} {m.extents.round(1)}  bed contact {flat:6.0f} mm2  watertight={m.is_watertight}"
              + ("" if (m.extents[:2] <= 240).all() else "  TOO BIG"))

    # ------------------------------------------------------------ preview
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    ORANGE, DARK = "#ff6a13", "#3a3a3a"

    def shade(m, c):
        k = np.clip(m.face_normals @ np.array([-.4, -.5, .8]), 0, 1) * 0.6 + 0.4
        return np.outer(k, matplotlib.colors.to_rgb(c))
    bm = box.mesh(box.body())
    bm.apply_translation((0, 0, -box.H - lidmod.GAP - lidmod.T))
    fig = plt.figure(figsize=(21, 15))

    def draw(ax, ms, lims, aspect, e, az, title):
        # one collection for the whole scene, big faces split up: matplotlib sorts by face depth, so this keeps the
        # painter's order right between parts
        tris, cols = [], []
        for m, c in ms:
            v, f = trimesh.remesh.subdivide_to_size(m.vertices, m.faces, 7.0)
            m = trimesh.Trimesh(v, f, process=False)
            tris.append(m.triangles); cols.append(shade(m, c))
        cols = np.concatenate(cols)
        ax.add_collection3d(Poly3DCollection(np.concatenate(tris), facecolors=cols, edgecolors=cols, linewidths=0.15))
        for f, l in zip((ax.set_xlim, ax.set_ylim, ax.set_zlim), lims):
            f(*l)
        ax.set_box_aspect(aspect); ax.view_init(e, az); ax.set_axis_off(); ax.set_title(title, fontsize=14)

    def arm(q, keep=lambda n, fr: True):
        ch = chain(q)
        out = []
        for n, (m, fr) in {**meshes, **dummies}.items():
            if keep(n, fr):
                w = m.copy(); w.apply_transform(ch[fr])
                out.append((w, DARK if ("case" in n or "horn" in n) else ORANGE))
        return out
    for k, (pn, e, az) in enumerate((("home (upright, forearm forward)", 14, -55), ("pick on the lid, claw down", 10, 15),
                                     ("over the front edge, down", 18, -125))):
        ax = fig.add_subplot(2, 3, k + 1, projection="3d")
        draw(ax, [(bm, "#d9a441"), (lm, ORANGE)] + arm(POSES[pn]), ((-125, 125), (-110, 230), (-60, 280)),
             (250, 340, 340), e, az, pn)
    ax = fig.add_subplot(2, 3, 4, projection="3d")          # the claw close up, half open
    draw(ax, arm((0, 0, 0, 0, 35), lambda n, fr: fr in "CD" or n == "j4_horn"),
         ((-55, 55), (L1 + L2 - 15, L1 + L2 + 120), (Z2 - 65, Z2 + 65)), (110, 135, 130), 18, -18, "claw (chela), half open")
    ax = fig.add_subplot(2, 3, 5, projection="3d")          # the arm from the side, reaching
    draw(ax, [(lm, ORANGE)] + arm(POSES["reach forward"]), ((-60, 60), (-60, 290), (-20, 170)), (120, 350, 190), 8, -14,
         "reach forward (side)")
    ax = fig.add_subplot(2, 3, 6, projection="3d")          # the carapace lid from above, turret on it
    draw(ax, [(lm, ORANGE), (meshes["turret"][0], ORANGE)], ((-125, 125), (-125, 125), (-20, 50)), (250, 250, 70), 62, -100,
         "lid-v3 carapace + turret")
    plt.tight_layout()
    plt.savefig(os.path.join(HERE, "preview.png"), dpi=80)
    print("torque", [round(t, 2) for t in TORQUE])
