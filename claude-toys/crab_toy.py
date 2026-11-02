"""Flexi King Crab ("킹크랩") for the Bambu Lab A1: one print, all PLA, legs and claws already jointed.

Character + a job: a little king crab that poses its 8 legs and 2 claws, and each claw has a cable notch so it sits on
the desk holding USB cables.

Joint (print-in-place, axis vertical, so every part lies flat and swings in the bed plane):
  - the body's post rises from the bed through the limb's ring and joins the body above it: the body overhangs the
    ring as a short bridge, 0.4 mm above it (stops the limb lifting);
  - the post has a 45 deg flange at the bottom and the ring's bore the matching cone (stops the limb dropping when you
    pick the crab up);
  - 0.5 mm horizontal gap, 0.9 mm at the first layer (post foot chamfered) so the first layer doesn't fuse them.
No snaps, no supports, no brim, no hardware.

Run:  uv run --with cadquery --with trimesh --with numpy --with shapely --with matplotlib --with manifold3d \\
        --with scipy --with networkx --with rtree python claude-toys/crab_toy.py
"""
import math
import os

import cadquery as cq
import numpy as np
import trimesh
from shapely import affinity
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))

H = 12.0                    # body height
T = 5.0                     # limb thickness
LIFT = 0.4                  # air between the limb's top and the body above it
GAP = 0.5                   # horizontal gap post <-> bore
POST = 2.6                  # post (neck) radius
FLANGE = 2.0                # flange height = radial step (45 deg)
RING = 6.6                  # limb ring outer radius
POCKET = RING + 0.6         # body cleared round each ring, from the bed up to T + LIFT
BODY = (47.0, 34.0)         # carapace half axes (x across, y front-back)
INSET = 3.0                 # post centre inside the carapace outline

# limbs: (angle of the post on the carapace, direction the limb points (deg), segment lengths, bend (deg), kind)
LEGS = [(a, d) for a, d in ((42, 42), (16, 12), (-12, -20), (-40, -52))]
CLAW_POST = 72.0            # front corners


def carapace():
    a, b = BODY
    return Polygon([(a * math.cos(t), b * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 120, endpoint=False)])


def on_rim(deg, side):
    """post centre: the carapace outline at deg (0 = +x, 90 = front), mirrored for side -1, pulled INSET inwards."""
    a, b = BODY
    t = math.radians(deg)
    x, y = a * math.cos(t), b * math.sin(t)
    n = np.array([x / a ** 2, y / b ** 2]); n /= np.linalg.norm(n)
    p = np.array([x, y]) - INSET * n
    return (side * p[0], p[1])


def strip(p, dirs_lens, w0, w1):
    """a tapered limb from p: a polyline of (direction deg, length) segments, width w0 -> w1, round joints."""
    pts = [np.array(p, float)]
    for d, L in dirs_lens:
        pts.append(pts[-1] + L * np.array([math.cos(math.radians(d)), math.sin(math.radians(d))]))
    total = sum(L for _, L in dirs_lens)
    parts, acc = [], 0.0
    for (q0, q1), (_, L) in zip(zip(pts, pts[1:]), dirs_lens):
        wa = w0 + (w1 - w0) * acc / total
        wb = w0 + (w1 - w0) * (acc + L) / total
        v = (q1 - q0) / L; n = np.array([-v[1], v[0]])
        parts.append(Polygon([q0 + n * wa / 2, q1 + n * wb / 2, q1 - n * wb / 2, q0 - n * wa / 2]))
        parts.append(Point(*q1).buffer(wb / 2))
        acc += L
    return unary_union(parts), pts[-1]


def leg(p, d, side):
    """walking leg: out along d, then kinked 22 deg down-back, tapering to a blunt tip."""
    dd = d if side > 0 else 180 - d
    kink = dd - 22 * side
    s, _ = strip(p, [(dd, 21.0), (kink, 19.0)], 9.5, 5.0)
    return unary_union([s, Point(p).buffer(RING)])


def claw(p, side):
    """claw: a short arm forward-out, then a big chela (the right one bigger, like a real king crab): a round palm and
    two thick fingers; between them a cable notch (Ø4.2 seat, 3.2 mouth) so a USB cable clicks in."""
    k = 1.0 if side > 0 else 0.85
    dd = 62 if side > 0 else 118
    v = np.array([math.cos(math.radians(dd)), math.sin(math.radians(dd))]); n = np.array([-v[1], v[0]]) * side
    arm, end = strip(p, [(dd, 13.0)], 10.0, 11.0)
    c = end + v * 11.0 * k
    ang = math.degrees(math.atan2(v[1], v[0]))
    palm = Point(*c).buffer(13.0 * k)
    upper = strip(c + n * 6.0 * k + v * 6 * k, [(ang - 6 * side, 17.0 * k)], 11.0 * k, 6.0 * k)[0]
    lower = strip(c - n * 6.0 * k + v * 6 * k, [(ang + 6 * side, 15.0 * k)], 10.0 * k, 6.0 * k)[0]
    shape = unary_union([arm, palm, upper, lower, Point(p).buffer(RING)])
    notch_c = c + v * 15.0 * k
    notch = unary_union([Point(*notch_c).buffer(2.1), strip(notch_c, [(ang, 20.0)], 3.2, 3.2)[0]])
    return shape.difference(notch).buffer(0.8).buffer(-0.8)


def limbs():
    out = []
    for side in (1, -1):
        for a, d in LEGS:
            p = on_rim(a, side)
            out.append(("leg", p, leg(p, d, side)))
        p = on_rim(CLAW_POST, side)
        out.append(("claw", p, claw(p, side)))
    return out


def extrude(poly, h, z0=0.0):
    w = cq.Workplane("XY").workplane(offset=z0).polyline(list(poly.exterior.coords)[:-1]).close()
    for hole in poly.interiors:
        w = w.polyline(list(hole.coords)[:-1]).close()
    return w.extrude(h)


def revolve(pts, at):
    return cq.Workplane("XZ").polyline(pts).close().revolve(360, (0, 0, 0), (0, 1, 0)).translate((at[0], at[1], 0))


def post_profile(r_neck, gap, z_top):
    """(r, z): flange r_neck + FLANGE at the bed, 45 deg in to the neck at z = FLANGE, straight up to z_top."""
    return [(0, 0), (r_neck + FLANGE + gap, 0), (r_neck + gap, FLANGE), (r_neck + gap, z_top), (0, z_top)]


def build():
    L = limbs()
    body = extrude(carapace(), H).edges(">Z").chamfer(3.0)
    for _, p, _ in L:
        body = body.cut(cq.Workplane("XY").center(*p).circle(POCKET).extrude(T + LIFT))
    for _, p, _ in L:
        post = revolve(post_profile(POST, 0, T + LIFT + 0.5), p)
        post = post.faces("<Z").edges().chamfer(0.4)
        body = body.union(post)
    # eyes: two stalks on the front of the carapace (top face prints up)
    for sx in (-1, 1):
        body = body.union(cq.Workplane("XY").workplane(offset=H - 3.5).center(sx * 9, 17).circle(4.0).extrude(6.5)
                          .faces(">Z").edges().fillet(1.5))
        body = body.cut(cq.Workplane("XY").workplane(offset=H + 2.0).center(sx * 9, 19.5).circle(1.6).extrude(2))
    parts = [("body", body)]
    for i, (k, p, poly) in enumerate(L):
        limb = extrude(poly, T)
        limb = limb.cut(revolve(post_profile(POST, GAP, T + 1), p).translate((0, 0, -0.01)))
        parts.append((f"{k}{i}", limb))
    return parts, L


def mesh(wp):
    path = os.path.join(HERE, "_tmp.stl")
    cq.exporters.export(wp, path)
    m = trimesh.load(path)
    os.remove(path)
    return m


def check(L):
    """2D clearances in the limb layer (z 0..T): limbs vs each other and vs the body's footprint there."""
    low = carapace()
    for _, p, _ in L:
        low = low.difference(Point(p).buffer(POCKET))
    low = unary_union([low] + [Point(p).buffer(POST + FLANGE) for _, p, _ in L])
    bad = 0
    for i, (k, p, poly) in enumerate(L):
        ring_free = poly.difference(Point(p).buffer(POST + FLANGE + GAP))
        d = ring_free.distance(low.difference(Point(p).buffer(POST + FLANGE + 0.01)))
        if d < 0.5:
            print(f"  {k}{i}: {d:.2f} mm to the body")
            bad += 1
        for j in range(i + 1, len(L)):
            dj = poly.distance(L[j][2])
            if dj < 0.8:
                print(f"  {k}{i} vs {L[j][0]}{j}: {dj:.2f} mm")
                bad += 1
    return bad


def preview(ms):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    fig = plt.figure(figsize=(12, 6))
    allm = trimesh.util.concatenate([m for _, m in ms])
    c, r = allm.bounds.mean(0), allm.extents.max() / 2
    for i, view in enumerate([(35, -65), (90, -90)]):
        ax = fig.add_subplot(1, 2, i + 1, projection="3d")
        for n, m in ms:
            col = np.array([0.86, 0.33, 0.18]) if n == "body" else np.array([0.93, 0.45, 0.25])
            light = np.clip(m.face_normals @ np.array([0.3, -0.5, 0.8]), 0.25, 1.0)[:, None]
            ax.add_collection3d(Poly3DCollection(m.triangles, facecolors=col * light))
        ax.set_xlim(c[0] - r, c[0] + r); ax.set_ylim(c[1] - r, c[1] + r); ax.set_zlim(c[2] - r, c[2] + r)
        ax.view_init(*view); ax.set_axis_off()
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "crab_preview.png"), dpi=110)


if __name__ == "__main__":
    parts, L = build()
    bad = check(L)
    ms = [(n, mesh(w)) for n, w in parts]
    for n, m in ms:
        if not m.is_watertight or len(m.split()) != 1:
            print(f"  {n}: watertight={m.is_watertight} bodies={len(m.split())}")
            bad += 1
    allm = trimesh.util.concatenate([m for _, m in ms])
    print(f"crab {allm.extents.round(1)}  parts {len(ms)}  problems {bad}")
    allm.export(os.path.join(HERE, "crab.stl"))
    preview(ms)
