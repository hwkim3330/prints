"""King Crab arm v2 ("깔끔한 킹크랩"): the same servos, joints and stack as crab.py, new clean shapes.

Everything mechanical comes from crab.py (servo/horn dicts S and M, the x stack, link lengths, servo frames, horn and
servo cuts), so a fit-coupon correction made there applies here too. What v2 changes is the look:
  - links: tapered, slightly bowed merus (upper arm) and carpus (forearm) side plates with soft rounded edges
    (a quarter round on the top face, a printable round = 45 deg start + round on the bed face)
  - one rounded web per link instead of two square spacers, its screw heads sunk into counterbores
  - idler pivots and web screws counterbored on the outer plates
  - chela: bulbous rounded palm, curved fingers that meet on one wavy bite line (two broad crushing bumps each,
    interleaved), the fixed finger tapering to the moving finger's thickness on a 45 deg underside
  - J3 / J4 servo covers: smooth shells over the MG996R on the upper arm and the MG90S on the forearm; they clamp the
    servos' spline-end ears with the ear screws (counterbored), so the links read as solid leg segments
  - turret: soft rounded-square flange; turntable: rounded disc and D-shaped shoulder cheeks round the J2 axis
Meant for one solid colour (purple PLA): the look comes from form and clean rounds, no accents.
Every part still prints flat, no supports, no brim, screws only. Rounds on bed faces start at 45 deg.

Run:  uv run --with cadquery --with trimesh --with numpy --with scipy --with networkx --with manifold3d \\
        --with rtree --with matplotlib --with shapely --with vtk python crab-arm/crab_v2.py
Writes crab-arm/v2/*.stl (in print orientation) and v2/preview.png (render_v2.py, VTK). crab.py's files are untouched.
"""
import itertools
import math
import os
import sys

import cadquery as cq
import numpy as np
import trimesh
from scipy.spatial import cKDTree
from shapely import affinity
from shapely.geometry import LineString, Polygon, box as sbox
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "v2")
os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, HERE)
import crab as C  # noqa: E402
from crab import (S, M, FIT, PT, PB, M3C, M3P, H_T, R_T, FLANGE, BASE_HOLES, L1, L2, XA, XB, Q, QP,  # noqa
                  F, FP, XK, XG, XD, XT, ZU, ZD, Z2, SF, sp, X, Y, Z, rot, tr, circ, ext, exz)

# ---------------------------------------------------------------- shape parameters (v2)
R_EDGE = 2.0                 # link plate edge round
J2R, J3R_U = 16.5, 23.5      # upper arm end radii (J2: under the disc clearance, J3: round the J3 servo ears)
J3R_F, J4R = 16.0, 13.5      # forearm end radii
WEB = 11.0                   # web height (z)
WEB_U = (32.0, 50.0)         # web screw stations along the upper arm (same as crab.py's spacers)
WEB_F = (30.0, 48.0)
CB = (6.4, 2.2)              # counterbore for M3 heads on outer faces: diameter, depth
CBP = (7.2, 2.0)             # idler pivots: room for the head + washer to turn
R_PALM, R_PALM_BED = 9.0, 7.0     # the claw's edge rounds, top (+x) and bed side (smaller where the outline is tight)
XTF = 12.55                  # the fingers' inner (-x) face: both fingers are XT - XTF = 12 thick
TIP = (106.0, -1.5)          # fixed finger tip in the claw frame (for the IK)


# ---------------------------------------------------------------- 2D helpers
def smooth(poly, r_convex, r_concave=None):
    p = poly.buffer(0)
    if r_concave:
        p = p.buffer(r_concave, 64).buffer(-r_concave, 64)
    return p.buffer(-r_convex, 64).buffer(r_convex, 64)


def catmull(pts, n=24, closed=True):
    """Centripetal-ish Catmull-Rom through pts (list of (y, z)); returns a dense point list."""
    P = np.asarray(pts, float)
    if closed:
        P = np.vstack([P[-1], P, P[0], P[1]])
    else:
        P = np.vstack([2 * P[0] - P[1], P, 2 * P[-1] - P[-2]])
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for t in np.linspace(0, 1, n, endpoint=False):
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    if not closed:
        out.append(P[-2])
    return [tuple(p) for p in out]


def link_outline(L, r0, r1, top, bot):
    """Side profile of a link from joint (0,0) to (L,0): end discs r0, r1 and a body whose upper/lower edges are
    top(t), bot(t) (half heights, t = 0..1). Smoothed: convex rounds 3, concave fillets 8."""
    ts = np.linspace(0, 1, 61)
    up = [(L * t, top(t)) for t in ts]
    lo = [(L * t, -bot(t)) for t in ts[::-1]]
    body = Polygon(up + lo)
    return smooth(unary_union([body, circ((0, 0), r0), circ((L, 0), r1)]), 3.0, 8.0)


def upper_outline():
    # merus: grows from the shoulder to the knee, dorsal edge bowed up, ventral edge with a slight waist
    return link_outline(L1, J2R, J3R_U,
                        lambda t: J2R + (J3R_U - J2R) * t + 2.8 * math.sin(math.pi * t),
                        lambda t: J2R + (J3R_U - J2R) * t - 3.2 * math.sin(math.pi * t))


def fore_outline():
    # carpus: stout at the elbow, tapering to the wrist, a soft dorsal hump
    return link_outline(L2, J3R_F, J4R,
                        lambda t: J3R_F + (J4R - J3R_F) * t + 2.4 * math.sin(math.pi * t ** 0.8),
                        lambda t: J3R_F + (J4R - J3R_F) * t - 2.0 * math.sin(math.pi * t))


def web_outline(st):
    """chamfered bar section (prints lying on a flat side: no rounded overhang at the bed)"""
    a, b = st[0] - WEB / 2, st[1] + WEB / 2
    h, c = WEB / 2, 2.0
    return Polygon([(a + c, -h), (b - c, -h), (b, -h + c), (b, h - c), (b - c, h), (a + c, h), (a, h - c), (a, -h + c)])


# ---- the chela (claw frame: origin on J4, y forward, z up at q4 = 0)
HINGE = (58.0, 12.0)         # J5 (crab.py: 44, 12): moved forward so the palm is long and the fingers short
R_ROOT = 17.0                # the moving finger's round root, turning in a socket of R_SOCK in the palm top
R_SOCK = R_ROOT + 0.8
B_ANG = -35.0                # the bite line starts on the root circle at this angle
BY0 = HINGE[0] + R_SOCK * math.cos(math.radians(B_ANG))
BZ0 = HINGE[1] + R_SOCK * math.sin(math.radians(B_ANG))
BY1, BZ1 = 107.0, -1.0       # bite line end = finger tips


def bite(y):
    """Where the fingers meet: a straight line from the root to the tips plus one soft wave (two broad bumps on each
    finger, interleaved), fading out at both ends."""
    t = np.clip((y - BY0) / (BY1 - BY0), 0, 1)
    env = np.sin(np.pi * t) ** 0.8
    return BZ0 + (BZ1 - BZ0) * t + 1.5 * env * np.sin(2 * np.pi * 2 * t)


BITE_Y = np.linspace(BY0, BY1, 81)


def _arc(c, r, a0, a1, n=40):
    return [(c[0] + r * math.cos(math.radians(a)), c[1] + r * math.sin(math.radians(a))) for a in np.linspace(a0, a1, n)]


def _keepout(p):
    """the palm keeps out of what the moving finger sweeps outside its root circle and of the forearm / J4 ears over
    the wrist's range (-65..+85 deg); every layer the same, so nothing is stepped"""
    sweep = unary_union([affinity.rotate(dactyl_outline(), a, origin=HINGE) for a in range(0, 46, 3)]).buffer(0.8)
    fo = affinity.translate(fore_outline(), -L2, 0)
    fo = unary_union([affinity.rotate(fo, -a, origin=(0, 0)) for a in range(-65, 86, 5)]).buffer(1.0)
    p = p.difference(sweep.difference(circ(HINGE, R_SOCK))).difference(fo).difference(circ((0, 0), 17.0))
    return max(p.geoms, key=lambda g: g.area) if p.geom_type == "MultiPolygon" else p


def palm_outline():
    """The palm (propodus manus): one smooth egg, rounds R_PALM all round, a rim round the finger's root socket."""
    egg = Polygon(catmull([(15.0, -9.0), (24.0, -20.5), (40.0, -26.5), (58.0, -26.5), (73.0, -20.0), (81.0, -9.0),
                           (80.0, 3.0), (72.0, 16.0), (62.0, 28.0), (48.0, 31.5), (32.0, 29.0), (20.0, 21.0), (14.0, 8.0)],
                          20)).buffer(0)
    p = _keepout(unary_union([egg, circ(HINGE, R_SOCK + 1.6)]))
    return smooth(p, R_PALM + 0.5, 4.0)


def pollex_outline():
    """The fixed finger: below the bite line, from inside the palm to the tip."""
    bl = [(y, float(bite(y))) for y in BITE_Y]
    low = catmull([(BY1, BZ1), (109.0, -2.4), (108.2, -4.6), (101.0, -8.4), (88.0, -14.5), (74.0, -20.0), (60.0, -22.0)],
                  16, closed=False)
    p = Polygon(low + [(52.0, -10.0), (56.0, BZ0)] + bl[:-1]).buffer(0)
    return smooth(_keepout(p), 2.6, 3.0)


def propodus_outline():
    return unary_union([palm_outline(), pollex_outline()])


def dactyl_outline():
    """Moving finger, closed: round root disc on J5, finger forward to the tip; its lower edge is the bite line."""
    bl = [(y, float(bite(y))) for y in BITE_Y]
    dors = catmull([(BY1, BZ1), (109.6, 0.8), (106.0, 5.0), (96.0, 11.5), (83.0, 18.5), (70.0, 24.2),
                    (HINGE[0], HINGE[1] + R_ROOT)], 16, closed=False)
    p = Polygon(bl + dors[1:] + _arc(HINGE, R_ROOT, 90, 180 + 60, 30)).buffer(0)
    return smooth(unary_union([p, circ(HINGE, R_ROOT)]), 1.8, 3.0)


def knuckle_outline():
    return smooth(unary_union([circ((0, 0), 12.5), sbox(0, -12.5, 26, 12.5)]), 3.0)


def palm_back_clear():
    """Region the palm must keep out of above the knuckle (x > XK[1]): forearm F's wrist end and the J4 servo's ears
    sweep round J4 within r 15."""
    return circ((0, 0), 15.5)



# ---------------------------------------------------------------- 3D: soft slabs (manifold), cutters (CadQuery)
import manifold3d as mf  # noqa: E402


def _cs(poly):
    polys = list(poly.geoms) if poly.geom_type == "MultiPolygon" else [poly]
    loops = []
    for p in polys:
        loops.append(np.asarray(p.exterior.coords)[:-1])
        loops += [np.asarray(h.coords)[:-1] for h in p.interiors]
    return mf.CrossSection(loops, mf.FillRule.EvenOdd)


def _round(h, r, printable):
    """inset of a rounded edge at height h from the face (0..r); printable: starts at 45 deg so no overhang"""
    if printable and h < 0.2929 * r:
        return 0.5858 * r - h
    return r - math.sqrt(max(0.0, r * r - (r - h) ** 2))


def _ring(pg, spacing=0.6):
    """exterior of a polygon resampled at even arc length, counter-clockwise, with outward unit normals"""
    from shapely.geometry.polygon import orient
    ring = np.asarray(orient(pg, 1.0).exterior.coords)[:-1]
    seg = np.linalg.norm(np.roll(ring, -1, 0) - ring, axis=1)
    s = np.concatenate([[0], np.cumsum(seg)])
    n = max(24, int(s[-1] / spacing))
    t = np.linspace(0, s[-1], n, endpoint=False)
    closed = np.vstack([ring, ring[:1]])
    p = np.column_stack([np.interp(t, s, closed[:, 0]), np.interp(t, s, closed[:, 1])])
    tg = np.roll(p, -1, 0) - np.roll(p, 1, 0)
    nr = np.column_stack([tg[:, 1], -tg[:, 0]])
    return p, nr / np.linalg.norm(nr, axis=1)[:, None]


def soft(poly, a0, a1, r0=0.0, r1=0.0, bed=None, axis="x", weight=None, k=7):
    """poly (shapely, in the plane across `axis`; no holes) extruded from a0 to a1 with rounded edges: r0 at a0, r1 at
    a1. bed = 0 / 1: that face goes on the bed and its round starts at 45 deg (no overhang). A smooth loft of offset
    rings; weight(points) -> 0..1 scales the rounds along the outline (big on the palm, small on the fingers).
    The outline must be smoothed with convex radii >= the local round."""
    poly = poly.buffer(0)
    hs = []
    if r0 > 0:
        hs += [(a0 + r0 * (1 - math.cos(u)), _round(r0 * (1 - math.cos(u)), r0, bed == 0)) for u in np.linspace(0, math.pi / 2, k)]
        if bed == 0:
            hs[0] = (a0, 0.5858 * r0)
            hs.insert(1, (a0 + 0.2929 * r0, 0.2929 * r0))
            hs = sorted(set(hs))
    else:
        hs.append((a0, 0.0))
    if r1 > 0:
        top = [(a1 - r1 * (1 - math.cos(u)), _round(r1 * (1 - math.cos(u)), r1, bed == 1)) for u in np.linspace(0, math.pi / 2, k)]
        if bed == 1:
            top[0] = (a1, 0.5858 * r1)
            top.insert(1, (a1 - 0.2929 * r1, 0.2929 * r1))
        hs += sorted(set(top))
    else:
        hs.append((a1, 0.0))
    hs = sorted(hs)
    out = []
    for pg in (poly.geoms if poly.geom_type == "MultiPolygon" else [poly]):
        p, nr = _ring(pg)
        w = np.ones(len(p)) if weight is None else np.clip(weight(p), 0, 1)
        n = len(p)
        dmax = max([d for h, d in hs] + [1e-6])
        # adapt: never round more than 0.85 x the local convex radius (fingertips, tight corners)
        rc = np.full(n, 1e9)
        for m4 in (1, 2, 4, 8):         # local convex radius at several scales
            a_, b_, c_ = np.roll(p, m4, 0), p, np.roll(p, -m4, 0)
            u_, v_ = b_ - a_, c_ - b_
            cr = u_[:, 0] * v_[:, 1] - u_[:, 1] * v_[:, 0]
            la, lb, lc = (np.linalg.norm(b_ - a_, axis=1), np.linalg.norm(c_ - b_, axis=1), np.linalg.norm(c_ - a_, axis=1))
            rc = np.minimum(rc, np.where(cr > 1e-9, la * lb * lc / (2 * np.abs(cr) + 1e-12), 1e9))
        cap = 0.85 * rc / dmax
        win = 9
        mn = np.min([np.roll(cap, j) for j in range(-win, win + 1)], axis=0)
        w = np.minimum(w, mn)
        w = np.mean([np.roll(w, j) for j in range(-win // 2, win // 2 + 1)], axis=0)
        w = np.minimum(w, cap)
        # and never more than 0.4 x the local width (narrow fingers, necks): ray-cast inwards to the far boundary
        bnd = pg.exterior
        wid = np.full(n, 1e9)
        for i in range(n):
            ray = LineString([p[i] - nr[i] * 0.3, p[i] - nr[i] * 60.0])
            hit = ray.intersection(bnd)
            if not hit.is_empty:
                pts_ = [hit] if hit.geom_type == "Point" else [g for g in getattr(hit, "geoms", []) if g.geom_type == "Point"]
                if pts_:
                    wid[i] = min(np.hypot(q.x - p[i][0], q.y - p[i][1]) for q in pts_)
        wcap = 0.4 * wid / dmax
        wcap = np.min([np.roll(wcap, j) for j in range(-win, win + 1)], axis=0)
        w = np.minimum(w, wcap)
        if os.environ.get("SOFT_DEBUG") and w.min() < 0.98:
            print(f"    soft: rounds reduced on {np.mean(w < 0.98):.0%} of the outline (min x{w.min():.2f})")
        rings = [p - nr * (d * w)[:, None] for h, d in hs]
        for rg in rings:
            if not Polygon(rg).is_valid:
                from shapely.validation import explain_validity
                raise AssertionError("offset ring self-intersects: " + explain_validity(Polygon(rg)))
        V = np.vstack([np.column_stack([rg, np.full(n, h)]) for rg, (h, d) in zip(rings, hs)])
        F = []
        idx = np.arange(n)
        for kk in range(len(hs) - 1):
            a_, b_ = kk * n + idx, kk * n + (idx + 1) % n
            c_, d_ = (kk + 1) * n + (idx + 1) % n, (kk + 1) * n + idx
            F += [np.column_stack([a_, b_, c_]), np.column_stack([a_, c_, d_])]
        for kk, flip in ((0, True), (len(hs) - 1, False)):
            tv, tf = trimesh.creation.triangulate_polygon(Polygon(rings[kk]))
            _, m_ = cKDTree(rings[kk]).query(tv)
            tf = m_[tf] + kk * n
            F.append(tf[:, ::-1] if flip else tf)
        m = trimesh.Trimesh(V, np.vstack(F), process=True)
        if m.volume < 0:
            m.invert()
        out.append(m)
    tm = out[0] if len(out) == 1 else union(*out)
    if axis == "x":         # (u, v, w) -> (x = w, y = u, z = v)
        tm.apply_transform(np.array([[0, 0, 1, 0], [1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1]], float))
    return tm


def _tm(m):
    mesh = m.to_mesh()
    return trimesh.Trimesh(np.asarray(mesh.vert_properties)[:, :3], np.asarray(mesh.tri_verts), process=False)


def _mf(t):
    return mf.Manifold(mf.Mesh(vert_properties=np.asarray(t.vertices, np.float32), tri_verts=np.asarray(t.faces, np.uint32)))


def union(*ms):
    return _tm(mf.Manifold.batch_boolean([_mf(m) for m in ms], mf.OpType.Add))


def diff(a, *bs):
    r = _mf(a)
    for b in bs:
        r = r - _mf(b)
    return _tm(r)


def inter(a, b):
    return _tm(_mf(a) ^ _mf(b))


def cqmesh(wp):
    import box
    return box.mesh(wp)


def cutter(apply, lo, hi, axis="x", half=200.0):
    """The material that `apply` (a function on a CadQuery solid) removes from a big block spanning lo..hi on axis."""
    if axis == "x":
        blk = ext(sbox(-half, -half, half, half), lo, hi)
    else:
        blk = exz(sbox(-half, -half, half, half), lo, hi)
    return diff(cqmesh(blk), cqmesh(apply(blk)))


def xcyl(c, r, x0, x1, n=40):
    """cylinder along x through (y, z) = c"""
    m = trimesh.creation.cylinder(r, x1 - x0, sections=n)
    m.apply_transform(rot(Y, 90))
    m.apply_translation(((x0 + x1) / 2, c[0], c[1]))
    return m


def zcyl(c, r, z0, z1, n=48):
    m = trimesh.creation.cylinder(r, z1 - z0, sections=n)
    m.apply_translation((c[0], c[1], (z0 + z1) / 2))
    return m


# ---------------------------------------------------------------- parts
def turret():
    """Fixed base on the lid: soft rounded-square flange (4 x M4 to the lid), a plain drum (the thrust ring) and the
    J1 servo box inside. Same interfaces as crab.turret()."""
    fl = smooth(sbox(-FLANGE[0] / 2, -FLANGE[0] / 2, FLANGE[0] / 2, FLANGE[0] / 2), 16.0)
    flange = soft(fl, 0, FLANGE[1], 0.6, 2.0, bed=0, axis="z")
    drum = diff(soft(circ((0, 0), R_T), 0, ZU - 0.5, 0, 0.8, axis="z"), zcyl((0, 0), R_T - 3.0, -1, ZU, 128))
    inner = cqmesh(C.turret())                  # box, ribs, servo window, pilots, M4 holes (crab.py's)
    core = inter(inner, zcyl((0, 0), R_T - 2.9, -1, ZU))
    t = union(flange, drum, core)
    holes = union(*[zcyl(h, 4.5 / 2, -1, FLANGE[1] + 1, 32) for h in BASE_HOLES])
    win = cutter(lambda b: b.cut(exz(sbox(-S["W"] / 2 - FIT, -(S["L"] - S["SPL"]) - FIT, S["W"] / 2 + FIT, S["SPL"] + FIT),
                                     -1, H_T + 1)), -0.5, H_T + 0.5, axis="z")
    return diff(t, holes, win)


def cheek_outline():
    prof = unary_union([circ((0, Z2), 22.0), sbox(-40.0, ZU + 1.0, 26.0, ZD + 3.0)]).convex_hull
    return smooth(prof, 4.0)


def turntable():
    """Rounded disc on the J1 horn; two D-shaped cheeks round the J2 axis (A holds J2 by its ears in a notch open at
    the top, B takes the idler), a low back wall ties them. All cuts as crab.turntable()."""
    disc = soft(circ((0, 0), R_T), ZU, ZD, 0.8, 2.0, bed=0, axis="z")
    prof = cheek_outline()
    a = soft(prof, XA - PB, XA, 1.5, 1.5)
    b = soft(prof, XB - PB, XB, 1.5, 1.5)
    wall = soft(smooth(sbox(-36.5, ZU + 1.0, -32.5, ZD + 11.0), 1.5), XB - PB + 1, XA - 1)
    t = union(disc, a, b, wall)
    t = inter(t, zcyl((0, 0), R_T - 1.2, ZU - 1, Z2 + 40, 96).union(zcyl((0, 0), R_T, ZU - 1, ZD + 0.5, 96)))
    c = S["C"]
    hx, hy = S["HOLES"]

    def cuts(blk):
        blk = blk.cut(exz(circ((0, 0), S["HD"] / 2 + FIT), ZU - 1, H_T + S["HORN"]))
        pts = [sp("j1", (r * math.cos(math.radians(q)), r * math.sin(math.radians(q)), 0))[:2] for r, q in S["HSCREW"]]
        under = lambda x: XA - PB - 2.5 < x < XA + 2.5 or XB - PB - 2.5 < x < XB + 2.5
        pts = [p for p in pts if not under(p[0])]
        blk = blk.cut(cq.Workplane("XY").pushPoints([tuple(p) for p in pts]).circle(1.2).extrude(ZD + 1))
        blk = blk.cut(exz(circ((0, 0), 3.5), ZU - 1, ZD + 1))
        blk = blk.cut(ext(sbox(-(S["L"] - S["SPL"]) - FIT, Z2 - S["W"] / 2 - FIT, S["SPL"] + FIT, Z2 + 40), XA - PT, XA + 1))
        blk = blk.cut(ext(unary_union([circ((-(c + sy * hx / 2), Z2 + sx * hy / 2), M3P / 2) for sx in (-1, 1) for sy in (-1, 1)]),
                          XA - 6, XA + 1))
        blk = blk.cut(ext(circ((0, Z2), M3P / 2), XB - PT - 1, XB + 1))
        return blk.cut(ext(sbox(-35.5, ZD - 1, -30.5, ZD + 8), XB - PT, XA + 1))
    return diff(t, cutter(cuts, ZU - 0.5, Z2 + 40, axis="z"))


def plate(outline, xr, bed, cuts=None, holes=(), cb=(), cbp=()):
    """A link side plate: outline extruded over xr, soft edges (bed = 0: xr[0] on the bed, 1: xr[1]), crab.py cuts,
    M3 clearance holes, counterbores on the face given by cb/cbp entries (y, z, face)."""
    p = soft(outline, xr[0], xr[1], R_EDGE, R_EDGE, bed=bed)
    rm = []
    if cuts:
        rm.append(cutter(cuts, xr[0] - 0.5, xr[1] + 0.5))
    for c, d in holes:
        rm.append(xcyl(c, d / 2, xr[0] - 1, xr[1] + 1, 32))
    for (y, z, face), (d, depth) in [(e, CB) for e in cb] + [(e, CBP) for e in cbp]:
        x0, x1 = (xr[0] - 1, xr[0] + depth) if face == 0 else (xr[1] - depth, xr[1] + 1)
        rm.append(xcyl((y, z), d / 2, x0, x1, 40))
    return diff(p, *rm) if rm else p


def upper_q():
    def cuts(blk):
        blk, _ = C.horn_cuts(blk, "j2_u", "S", Q)
        return C.servo_cuts(blk, "j3", "S", Q)
    return plate(upper_outline(), Q, 1, cuts, [((y, 0), M3C) for y in WEB_U], cb=[(y, 0, 1) for y in WEB_U])


def upper_qp():
    return plate(upper_outline(), QP, 0, None, [((0, 0), M3C), ((L1, 0), M3C)] + [((y, 0), M3C) for y in WEB_U],
                 cb=[(y, 0, 0) for y in WEB_U], cbp=[(0, 0, 0), (L1, 0, 0)])


def fore_f():
    def cuts(blk):
        blk, _ = C.horn_cuts(blk, "j3_f", "S", F)
        return C.servo_cuts(blk, "j4", "M", F)
    return plate(fore_outline(), F, 0, cuts, [((y, 0), M3C) for y in WEB_F], cb=[(y, 0, 1) for y in WEB_F])


def fore_fp():
    return plate(fore_outline(), FP, 0, None, [((0, 0), M3P), ((L2, 0), M3C)] + [((y, 0), M3C) for y in WEB_F],
                 cb=[(y, 0, 0) for y in WEB_F], cbp=[(L2, 0, 0)])


# ---- J3 servo cover: a smooth shell over the MG996R on the upper arm's outer plate, so the merus reads as one leg
# segment. It clamps the servo's two J3-end ears with the same M3 screws (counterbored from the top; M3 x 16), the
# J2-end ears are screwed first as before (their heads and the lead sit in the cover's open end).
def servo_cover(s, face, sx, L, outline, half=None, top=2.4):
    """Shell over a servo standing on a link's outer plate (face = plate's outer face x, sx = tab undersides x, servo
    spline at y = L, case towards the link's start). Clamps the spline-end ear(s) with the ear screw(s), counterbored
    from the top; the far-end ears are screwed first and sit in the cover's open end with the lead."""
    yc = L - s["C"]
    w2 = s["W"] / 2 + 0.5
    half = half or w2 + 2.4
    cy = (yc - s["SPAN"] / 2 - 2.6, yc + s["SPAN"] / 2 + 2.9)
    x0, x1 = face + 0.25, sx + s["BOT"] + 0.5 + top
    fp = smooth(smooth(sbox(cy[0], -half, cy[1], half), min(6.0, half - 0.5)).intersection(outline.buffer(-1.2)), min(4.0, half - 1))
    c = soft(fp, x0, x1, 1.0, min(6.0, half - 1.5), bed=1)
    ear = (yc - s["SPAN"] / 2 - 0.25, yc + s["SPAN"] / 2 + 0.25)
    case = (L - (s["L"] - s["SPL"]) - 0.5, L + s["SPL"] + 0.5)
    rm = [soft(sbox(ear[0], -w2, ear[1], w2), x0 - 1, sx),                       # ears (the cover rests on them)
          soft(sbox(case[0], -w2, case[1], w2), x0 - 1, x1 - top),               # case
          soft(sbox(ear[0], -w2, case[0] + 0.1, w2), x0 - 1, x1 - top),          # far end: screw heads + lead
          soft(sbox(cy[0] - 1, -min(4.0, w2 - 1), ear[0] + 0.1, min(4.0, w2 - 1)), x0 - 1, x0 + 4.0)]   # lead out
    hx, hy = s["HOLES"]
    for sz in ((-1, 1) if hy else (0,)):
        h = (yc + hx / 2, sz * hy / 2)
        rm += [xcyl(h, M3C / 2 if s is S else 1.2, x0 - 1, x1 + 1), xcyl(h, (CB[0] if s is S else 4.6) / 2, sx + 6.0, x1 + 1)]
    return diff(c, *rm)


def cover_j3():
    """MG996R J3 on the upper arm: the merus reads as one leg segment. M3 x 16 through the cover into Q."""
    return servo_cover(S, Q[1], C.S3X, L1, upper_outline(), half=12.6)


def cover_j4():
    """MG90S J4 on the forearm. M2 x 10 through the cover into F."""
    return servo_cover(M, F[1], C.S4X, L2, fore_outline(), top=2.0)


def web(st, xr):
    """one rounded bar between the two plates of a link (replaces crab.py's two square spacers); M3 pilots 12 deep
    in both ends at the two stations"""
    w = soft(web_outline(st), xr[0], xr[1])
    rm = [xcyl((y, 0), M3P / 2, xr[0] - 1, xr[0] + 12) for y in st] + [xcyl((y, 0), M3P / 2, xr[1] - 12, xr[1] + 1) for y in st]
    return diff(w, *rm)


# ---- claw
Y_RAMP = 108.0 - (XTF - XK[0])      # the fixed finger's underside rises at 45 deg from here to XTF at the tip


def ramp_cut():
    pg = Polygon([(Y_RAMP, XK[0] - 1), (130.0, XK[0] - 1), (130.0, XK[0] + 130.0 - Y_RAMP)])   # (y, x)
    m = trimesh.creation.extrude_polygon(pg, 120.0)          # in (y, x, z) -> swap to (x, y, z)
    m.apply_translation((0, 0, -60.0))
    m.apply_transform(np.array([[0, 1, 0, 0], [1, 0, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]], float))
    m.fix_normals()
    return m


def claw():
    palm = union(soft(palm_outline(), XK[0], XT, R_PALM_BED, R_PALM, bed=0),
                 soft(pollex_outline(), XK[0], XT, 2.5, 2.5, bed=0))
    palm = diff(palm, ramp_cut())
    knuckle = soft(knuckle_outline(), XK[0], XK[1], 1.5, 1.5, bed=0)
    c = union(palm, knuckle)
    s = M
    yc = HINGE[0] - s["C"]

    def cuts(blk):
        blk, pts = C.horn_cuts(blk, "j4_c", "M", XK, centre=5.0, centre_depth=3.0, screw_d=2.2)
        fl = C.x_of("j4_c", M["HORN"])
        blk = blk.cut(ext(unary_union([circ(p, 2.4) for p in pts]), XK[0] - 1, fl - 6))
        blk = blk.cut(ext(circ((0, 0), M3P / 2), XK[0] - 1, XK[0] + 10))
        blk = blk.cut(ext(sbox(yc - s["SPAN"] / 2 - FIT, HINGE[1] - s["W"] / 2 - FIT, yc + s["SPAN"] / 2 + FIT,
                               HINGE[1] + s["W"] / 2 + FIT), XG, XT + 1))
        blk = blk.cut(ext(sbox(HINGE[0] - (s["L"] - s["SPL"]) - FIT, HINGE[1] - s["W"] / 2 - FIT, HINGE[0] + s["SPL"] + FIT,
                               HINGE[1] + s["W"] / 2 + FIT), XG - s["BOT"] - 0.3, XT + 1))
        blk = blk.cut(ext(unary_union([circ((yc + sy * s["HOLES"][0] / 2, HINGE[1]), s["PILOT"] / 2) for sy in (-1, 1)]),
                          XG - 8, XG + 0.1))
        # J5 lead: a closed tunnel from the case pocket out of the palm's back, between the forearm plates
        blk = blk.cut(ext(sbox(0, 12.8, HINGE[0] - (s["L"] - s["SPL"]), HINGE[1] + s["W"] / 2 + FIT),
                          XG - s["BOT"] + 2, XG - s["BOT"] + 12))
        # the moving finger's socket and everything it sweeps (0..45 deg open), 0.8 mm all round
        sweep = unary_union([affinity.rotate(dactyl_outline(), a, origin=HINGE) for a in range(0, 46, 3)]).buffer(0.8)
        return blk.cut(ext(unary_union([sweep, circ(HINGE, R_SOCK)]), XTF - 1.0, XT + 1))
    return diff(c, cutter(cuts, XK[0] - 0.5, XT + 0.5))


def dactyl():
    """moving finger, XTF..XT (12 thick); the J5 horn drops into a pocket open to its -x face, screws from +x"""
    d = soft(dactyl_outline(), XTF, XT, 3.5, 2.5, bed=1)

    def cuts(blk):
        blk = blk.cut(ext(C.horn_outline("j5", "M"), XTF - 1, C.x_of("j5", M["HORN"])))
        blk = blk.cut(ext(circ(HINGE, M["BOSS"][0] + 0.6), XTF - 1, XG + M["BOSS"][1] + 1.5))     # clear of the boss
        blk, _ = C.horn_cuts(blk, "j5", "M", (XTF, XT), centre=5.0, screw_d=2.2)
        return blk
    return diff(d, cutter(cuts, XTF - 0.5, XT + 0.5))


# ---------------------------------------------------------------- printed servo dummies (assemble and pose by hand)
# A dummy is the servo's envelope (case, ears with the same screw holes, a flat-sided boss), so it goes into the same
# window / pocket with the same ear screws and the same clearance. The link turns on a printed HUB: the horn's outline
# (it drops into the link's horn pocket and takes the horn screws) with a sleeve under it. The axle is one screw on
# the spline axis, clamping the hub against the dummy's boss: tighten it until the joint holds a pose by hand.
#   J1, J2, J3, J5: screw from the link side through the link's horn-centre hole and the hub into a pilot in the boss
#   J4: the claw's centre recess is blind, so the screw comes from the dummy's bottom (counterbore + washer) through a
#       clearance bore and bites into the hub
DUMMY_JOINTS = {   # joint: (kind, axle from "top" or "bottom", boss top z, hub sleeve outline: "disc" r / "horn")
    "j1": ("S", "top"), "j2": ("S", "top"), "j3": ("S", "top"), "j4": ("M", "bottom"), "j5": ("M", "top")}
AXLE = {"S": dict(d=3.0, pilot=2.6, clear=3.4, cb=(8.0, 3.0)), "M": dict(d=2.0, pilot=1.7, clear=2.4, cb=(8.0, 3.0))}


def _boss_top(s):
    return s["TOP"] + 2.0 if s is S else s["BOSS"][1]


def dummy_servo(kind, axle):
    """printed servo dummy in the servo frame (prints lying on its -x side)"""
    s = S if kind == "S" else M
    bt = _boss_top(s)
    br = s["BOSS"][0]
    prof = unary_union([sbox(-s["SPL"], -s["BOT"], s["L"] - s["SPL"], s["TOP"]),
                        sbox(s["C"] - s["SPAN"] / 2, 0, s["C"] + s["SPAN"] / 2, s["TAB"]),
                        sbox(-br, s["TOP"] - 0.5, br, bt)])
    prof = smooth(prof, 1.0)            # convex corners only: a concave fillet would stand proud of the envelope
    d = soft(prof, -s["W"] / 2, s["W"] / 2, 0.8, 0.8, bed=0)
    hx, hy = s["HOLES"]
    rm = [zcyl((sx * hy / 2, s["C"] + sy * hx / 2), (M3C if s is S else 2.4) / 2, -1, s["TAB"] + 1, 24)
          for sx in ((-1, 1) if hy else (0,)) for sy in (-1, 1)]
    if axle == "top":
        rm.append(zcyl((0, 0), AXLE[kind]["pilot"] / 2, bt - 12.0, bt + 1, 24))
    else:                                  # M3 from the bottom: clearance bore + counterbore for head and washer
        rm += [zcyl((0, 0), AXLE["S"]["clear"] / 2, -s["BOT"] - 1, bt + 1, 24),
               zcyl((0, 0), AXLE["S"]["cb"][0] / 2, -s["BOT"] - 1, -s["BOT"] + AXLE["S"]["cb"][1], 32)]
    return diff(d, *rm)


def dummy_hub(kind, axle):
    """printed horn replacement in the servo frame: horn outline from the boss top (+0.3) to the horn top"""
    s = S if kind == "S" else M
    z0 = _boss_top(s) + 0.3
    if s is S:
        h = union(soft(circ((0, 0), 9.0), z0, s["HORN"] - s["HT"] + 0.01, 0, 0, axis="z"),
                  soft(circ((0, 0), s["HD"] / 2), s["HORN"] - s["HT"], s["HORN"], 0.4, 0.4, bed=1, axis="z"))
    else:
        a, tip = s["ARM"]
        arm = unary_union([circ((0, 0), s["HD"] / 2), circ((0, -a), tip / 2)]).convex_hull
        h = soft(arm, z0, s["HORN"], 0.3, 0.3, bed=1, axis="z")
    pts = [(r * math.cos(math.radians(t)), -r * math.sin(math.radians(t))) for r, t in s["HSCREW"]]
    rm = [zcyl(p, 1.7 / 2, z0 - 1, s["HORN"] + 1, 16) for p in pts]          # M2 horn screws bite here
    if axle == "top":
        rm.append(zcyl((0, 0), AXLE["S" if s is S else "M"]["clear"] / 2, z0 - 1, s["HORN"] + 1, 24))
    else:
        rm.append(zcyl((0, 0), AXLE["S"]["pilot"] / 2, z0 - 1, s["HORN"] + 1, 24))
    return diff(h, *rm)


def build_dummies():
    """{name: (mesh in its mounting frame, frame letter)} for the 5 dummies and 5 hubs"""
    out = {}
    for n, kind, on, drv, sfm in SERVOS:
        k, ax = DUMMY_JOINTS[n]
        d = dummy_servo(k, ax); d.apply_transform(sfm)
        h = dummy_hub(k, ax); h.apply_transform(HORN_IN[n])
        out["dummy_" + n] = (d, on)
        out["hub_" + n] = (h, drv)
    return out


# ---------------------------------------------------------------- assembly, kinematics
def build():
    return {"turret": (turret(), "W"), "turntable": (turntable(), "T"),
            "upper_q": (upper_q(), "U"), "upper_qp": (upper_qp(), "U"), "cover_j3": (cover_j3(), "U"), "web_u": (web(WEB_U, (QP[1], Q[0])), "U"),
            "fore_f": (fore_f(), "F"), "fore_fp": (fore_fp(), "F"), "cover_j4": (cover_j4(), "F"), "web_f": (web(WEB_F, (FP[1], F[0])), "F"),
            "claw": (claw(), "C"), "dactyl": (dactyl(), "D")}


SF["j5"] = C.frame((XG, HINGE[0], HINGE[1]), Z, -Y, X)        # J5 at the v2 hinge (crab.SF is only used here)


def chain(q):
    """crab.chain with the v2 hinge"""
    ch = C.chain(q[:4] + (0,))
    ch["D"] = ch["C"] @ tr(0, *HINGE) @ rot(X, q[4]) @ tr(0, -HINGE[0], -HINGE[1])
    return ch


SERVOS = [s if s[0] != "j5" else ("j5", "M", "C", "D", SF["j5"]) for s in C.SERVOS]
HORN_IN = {**C.HORN_IN, "j5": SF["j5"]}


def ik(y, z, claw_deg, yaw=0.0, pincer=0.0):
    a = math.radians(claw_deg)
    wy = y - (TIP[0] * math.cos(a) - TIP[1] * math.sin(a))
    wz = z - (TIP[0] * math.sin(a) + TIP[1] * math.cos(a)) - Z2
    c3 = (wy * wy + wz * wz - L1 * L1 - L2 * L2) / (2 * L1 * L2)
    q3 = -math.acos(max(-1.0, min(1.0, c3)))
    q2 = math.atan2(wz, wy) - math.atan2(L2 * math.sin(q3), L1 + L2 * math.cos(q3))
    q2, q3 = math.degrees(q2), math.degrees(q3)
    return (yaw, round(q2, 1), round(q3, 1), round(claw_deg - q2 - q3, 1), pincer)


POSES = {
    "home (upright, forearm forward)": (0, 90, -90, 0, 0),
    "reach forward": (0, 20, -15, 0, 40),
    "pick on the lid, claw down": ik(85, 4, -90, pincer=45),
    "over the front edge, down": ik(150, -30, -75, pincer=30),
    "tucked": (0, 115, -145, 50, 0),
    "low to the side": (90, 15, -40, -40, 20),
    "high, claw up": (-60, 100, -20, 80, 45),
}
ORIENT = {"cover_j3": (0, 90), "cover_j4": (0, 90), "turret": (0, 0), "turntable": (0, 0), "upper_q": (0, 90), "upper_qp": (0, -90), "web_u": (0, 0),
          "fore_f": (0, -90), "fore_fp": (0, -90), "web_f": (0, 0), "claw": (0, -90), "dactyl": (0, 90)}


def lay(m, rx=0.0, ry=0.0):
    m = m.copy()
    if rx:
        m.apply_transform(rot(X, rx))
    if ry:
        m.apply_transform(rot(Y, ry))
    m.apply_translation([128 - m.bounds.mean(0)[0], 128 - m.bounds.mean(0)[1], -m.bounds[0][2]])
    return m


def scene_meshes():
    os.environ["ARM"] = "crab"
    import box  # noqa
    import lid as lidmod
    parts = build()
    dummies = {}
    for n, kind, on, drv, sfm in SERVOS:
        body, horn = C.servo_dummy(kind)
        b = body.copy(); b.apply_transform(sfm)
        h = horn.copy(); h.apply_transform(HORN_IN[n])
        dummies[n + "_case"] = (b, on)
        dummies[n + "_horn"] = (h, drv)
    lm = cqmesh(lidmod.lid())
    lm.apply_translation((0, 0, -(lidmod.GAP + lidmod.T)))
    body = trimesh.load(os.path.join(HERE, "..", "sensor-box", "v11", "body.stl"))
    body.apply_translation(-np.array([*body.bounds.mean(0)[:2], body.bounds[1][2]]) + (0, 0, -(lidmod.GAP + lidmod.T)))
    return parts, dummies, lm, body


if __name__ == "__main__":
    print(f"x stack (crab.py): Q {Q}  Q' {QP}  F {F}  F' {FP}  knuckle {XK}  dactyl {XD}  J2 z {Z2:.1f}")
    parts, dummies, lm, body = scene_meshes()
    meshes = {}
    for n, (m, fr) in parts.items():
        bodies = len(m.split(only_watertight=False))
        meshes[n] = (m, fr)
        print(f"{n:10s} {m.extents.round(1)}  watertight={m.is_watertight}  bodies={bodies}  {m.volume / 1000:6.1f} cm3")
    allm = {**meshes, **dummies, "lid": (lm, "W")}
    allowed = {("j1_case", "turret"), ("j1_horn", "turntable"), ("j2_case", "turntable"), ("j2_horn", "upper_q"),
               ("j3_case", "upper_q"), ("j3_horn", "fore_f"), ("j4_case", "fore_f"), ("j4_horn", "claw"),
               ("j5_case", "claw"), ("j5_horn", "dactyl"), ("j1_case", "j1_horn"), ("j2_case", "j2_horn"),
               ("j3_case", "j3_horn"), ("j4_case", "j4_horn"), ("j5_case", "j5_horn"), ("turret", "lid"),
               ("web_u", "upper_q"), ("web_u", "upper_qp"), ("cover_j3", "j3_case"), ("cover_j4", "j4_case"), ("web_f", "fore_f"), ("web_f", "fore_fp")}
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
        print(f"pose {pname:34s} q={q}  tip {tip.round(0)}  " + ("OK" if not bad else "HITS: " + ", ".join(bad)))
        probs += len(bad)
    print("collision problems:", probs)

    # torque: same model as crab.py (arm straight out, 50 g in the claw)
    PLA, FILL = 1.24e-3, {"claw": 0.36}
    ch = chain((0, 0, 0, 0, 0))
    LEVEL = {"U": 2, "F": 3, "C": 4, "D": 4}
    load = [(m.volume * PLA * FILL.get(n, 0.48), (ch[fr] @ np.append(m.center_mass, 1))[1], LEVEL[fr])
            for n, (m, fr) in meshes.items() if fr in LEVEL]
    load += [(55 + 3, L1, 3), (13.4 + 1, L1 + L2, 4), (13.4 + 1, L1 + L2 + HINGE[0] - M["C"], 5)]
    load += [(12, L1 / 2, 2), (8, L1 + L2 / 2, 3), (5, L1 + L2 + 40, 4), (50, L1 + L2 + 82, 5)]
    total = sum(g for g, y, lv in load)
    tq = lambda j, ay: sum(g * (y - ay) for g, y, lv in load if lv >= j) / 1e4
    t2, t3, t4 = tq(2, 0), tq(3, L1), tq(4, L1 + L2)
    print(f"moving mass {total:.0f} g (incl. 50 g payload), arm straight out")
    for n, t, lim in (("J2 shoulder (MG996R)", t2, 9.0), ("J3 elbow (MG996R)", t3, 9.0), ("J4 wrist (MG90S)", t4, 1.8)):
        print(f"  {n:22s} {t:4.2f} kg cm of {lim} stall = {t / lim:.0%}")

    # export, print checks
    for n, (m, fr) in meshes.items():
        o = lay(m, *ORIENT[n])
        o.export(os.path.join(OUT, n + ".stl"))
        flat = o.area_faces[(o.face_normals[:, 2] < -0.999) & (o.triangles_center[:, 2] < 0.01)].sum()
        # overhang: downward faces above the bed steeper than 45 deg from vertical (area, mm2)
        dn = (o.face_normals[:, 2] < -0.7072) & (o.triangles_center[:, 2] > 0.3)
        print(f"print {n:10s} {o.extents.round(1)}  bed contact {flat:6.0f} mm2  overhang>45 {o.area_faces[dn].sum():6.0f} mm2"
              + ("" if (o.extents[:2] <= 240).all() else "  TOO BIG"))
    # ------------------------------------------------------------ printed servo dummies
    print("printed servo dummies (hand-posed arm):")
    dm = build_dummies()
    for n, (m, fr) in dm.items():
        print(f"  {n:9s} {m.extents.round(1)}  watertight={m.is_watertight}  bodies={len(m.split(only_watertight=False))}"
              f"  {m.volume / 1000:5.1f} cm3")
    pairs_ok = {("dummy_" + n, part) for n, part in [("j1", "turret"), ("j2", "turntable"), ("j3", "upper_q"), ("j4", "fore_f"),
                                                      ("j5", "claw"), ("j3", "cover_j3"), ("j4", "cover_j4")]}
    pairs_ok |= {("hub_" + n, part) for n, part in [("j1", "turntable"), ("j2", "upper_q"), ("j3", "fore_f"), ("j4", "claw"),
                                                     ("j5", "dactyl")]}
    pairs_ok |= {("dummy_" + n, "hub_" + n) for n in DUMMY_JOINTS} | {("turret", "lid")}
    pairs_ok |= {p for p in allowed if not any(("_case" in x or "_horn" in x) for x in p)}
    allm_d = {**meshes, **dm, "lid": (lm, "W")}
    probs_d = 0
    for pname, q in POSES.items():
        ch = chain(q)
        world = {}
        for n, (m, fr) in allm_d.items():
            w = m.copy(); w.apply_transform(ch[fr]); world[n] = w
        bad = []
        for a, b in itertools.combinations(world, 2):
            ma, mb = world[a], world[b]
            if (ma.bounds[0] > mb.bounds[1]).any() or (mb.bounds[0] > ma.bounds[1]).any():
                continue
            v = trimesh.boolean.intersection([ma, mb], engine="manifold").volume
            lim = 0.5 if ((a, b) in pairs_ok or (b, a) in pairs_ok) else 0.05
            if v > lim:
                bad.append(f"{a}/{b} {v:.1f} mm3")
        print(f"  pose {pname:34s} " + ("OK" if not bad else "HITS: " + ", ".join(bad)))
        probs_d += len(bad)
    print("  collision problems with dummies:", probs_d)
    # same envelope as the servo dummy used for the real-servo check (so the same clearances in every pocket)
    for n, kind, on, drv, sfm in SERVOS:
        real, _ = C.servo_dummy(kind)
        k = dm["dummy_" + n][0].copy(); k.apply_transform(np.linalg.inv(sfm))
        out_ = diff(k, real).volume
        print(f"  {n} dummy outside the real servo envelope: {out_:.2f} mm3")
    for n, (m, fr) in dm.items():
        j = n.split("_")[1]
        sfm = dict((x[0], x[4]) for x in SERVOS)[j] if n.startswith("dummy") else HORN_IN[j]
        loc = m.copy(); loc.apply_transform(np.linalg.inv(sfm))                    # back to the servo frame
        o = lay(loc, *((0, -90) if n.startswith("dummy") else (180, 0)))
        o.export(os.path.join(OUT, n + ".stl"))
        flat = o.area_faces[(o.face_normals[:, 2] < -0.999) & (o.triangles_center[:, 2] < 0.01)].sum()
        dn = (o.face_normals[:, 2] < -0.7072) & (o.triangles_center[:, 2] > 0.3)
        print(f"  print {n:9s} {o.extents.round(1)}  bed contact {flat:5.0f} mm2  overhang>45 {o.area_faces[dn].sum():4.0f} mm2")

    import render_v2
    render_v2.preview(meshes, dummies, lm, body, POSES, chain, os.path.join(OUT, "preview.png"))

