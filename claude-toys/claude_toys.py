"""Claude-shaped desk toys for the Bambu Lab A1, PLA (orange), no supports, no brim.

  clawd.stl   Clawd, the Claude Code pixel mascot, as a chunky voxel figure: 7-wide body, two eye pockets,
              stubby arms, a pair of legs front and back (8 in all, a little king crab). Stands on its legs.
  spark.stl   the Claude spark (asterisk of rounded rays) as a 4 mm keychain with a loop on one ray.

Run:  uv run --with cadquery --with trimesh --with numpy --with shapely --with matplotlib --with manifold3d \\
        python claude-toys/claude_toys.py
"""
import math
import os

import cadquery as cq
import numpy as np
import trimesh
from shapely import affinity
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
U = 6.0                     # one pixel
DEPTH = 5                   # body depth in pixels

# front view of Clawd, top row first: X body, E eye pocket, . empty
CLAWD = [
    ".XXXXXXX.",
    ".XEXXXEX.",
    "XXXXXXXXX",
    ".XXXXXXX.",
    ".X.X.X.X.",
]
EYE_DEPTH = 3.0             # pockets for a black marker or a dab of paint


def clawd():
    rows = len(CLAWD)
    body = None
    for r, line in enumerate(CLAWD):
        z = (rows - 1 - r) * U
        for c, ch in enumerate(line):
            if ch == ".":
                continue
            legs = r == rows - 1
            ys = [0.0, (DEPTH - 1) * U] if legs else [0.0]      # legs only at the front and back pixel rows
            for y in ys:
                d = U if legs else DEPTH * U
                b = cq.Workplane("XY").box(U, d, U, centered=False).translate((c * U, y, z))
                body = b if body is None else body.union(b)
    # arms stick out one pixel on row 2: give them a 45 deg underside so they print without supports
    rows_z = (rows - 1 - 2) * U
    for c in (0, len(CLAWD[0]) - 1):
        x_in = U if c == 0 else c * U
        x_out = 0.0 if c == 0 else (c + 1) * U
        prof = (cq.Workplane("XZ").polyline([(x_in, rows_z - U), (x_in, rows_z), (x_out, rows_z)]).close()
                .extrude(-DEPTH * U))
        body = body.union(prof)
    for r, line in enumerate(CLAWD):
        for c, ch in enumerate(line):
            if ch == "E":
                z = (rows - 1 - r) * U
                body = body.cut(cq.Workplane("XY").box(U * 0.7, EYE_DEPTH, U * 1.4, centered=False)
                                .translate((c * U + U * 0.15, -0.01, z - U * 0.2)))
    return body.clean()


RAYS = [1.00, 0.78, 0.92, 0.70, 0.96, 0.82, 0.74, 0.98, 0.80, 0.90, 0.72, 0.86]   # irregular, like the logo
R_SPARK, T_SPARK = 30.0, 4.0


def spark():
    rays = []
    for k, f in enumerate(RAYS):
        L = R_SPARK * f
        ray = Polygon([(0, -5.0), (L - 2.4, -2.4), (L - 2.4, 2.4), (0, 5.0)]).union(Point(L - 2.4, 0).buffer(2.4))
        rays.append(affinity.rotate(ray, 360 / len(RAYS) * k + 4 * math.sin(k * 1.7), origin=(0, 0)))
    s = unary_union(rays + [Point(0, 0).buffer(9.0)])
    loop = Point(R_SPARK + 2.5, 0).buffer(5.0).difference(Point(R_SPARK + 2.5, 0).buffer(2.4))
    s = unary_union([s, loop]).buffer(0.4).buffer(-0.4)
    s = s.simplify(0.05)
    w = cq.Workplane("XY").polyline(list(s.exterior.coords)[:-1]).close()
    for hole in s.interiors:
        w = w.polyline(list(hole.coords)[:-1]).close()
    return w.extrude(T_SPARK)


def mesh(wp, name):
    path = os.path.join(HERE, name + ".stl")
    cq.exporters.export(wp, path)
    m = trimesh.load(path)
    m.apply_translation(-m.bounds[0])
    m.export(path)
    z0 = m.bounds[0][2]
    bed = m.area_faces[np.abs(m.triangles[:, :, 2] - z0).max(1) < 0.01].sum()
    print(f"{name:6s} {m.extents.round(1)}  watertight={m.is_watertight}  bodies={len(m.split())}  bed {bed:.0f} mm2")
    return m


def preview(ms):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    fig = plt.figure(figsize=(10, 5))
    for i, (m, title) in enumerate(ms):
        ax = fig.add_subplot(1, len(ms), i + 1, projection="3d")
        n = m.face_normals
        light = np.clip(n @ np.array([0.3, -0.6, 0.75]), 0.15, 1.0)[:, None]
        ax.add_collection3d(Poly3DCollection(m.triangles, facecolors=np.array([0.85, 0.47, 0.34]) * light))
        c, r = m.bounds.mean(0), m.extents.max() / 2
        ax.set_xlim(c[0] - r, c[0] + r); ax.set_ylim(c[1] - r, c[1] + r); ax.set_zlim(c[2] - r, c[2] + r)
        ax.view_init(18, -100); ax.set_axis_off(); ax.set_title(title)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "preview.png"), dpi=110)


if __name__ == "__main__":
    a = mesh(clawd(), "clawd")
    b = mesh(spark(), "spark")
    preview([(a, "Clawd"), (b, "Claude spark keychain")])
