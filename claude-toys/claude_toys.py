"""Claude spark fidget spinner for the Bambu Lab A1, PLA, print-in-place (no bearing, no snaps, no supports, no brim).

The rotor is the Claude spark (rounded rays round a disc), 8 mm thick. The hub is a spool (hourglass in section):
Ø22 faces top and bottom, a 45 deg cone in to a Ø14 neck at mid-height and out again. The rotor's bore is the matching
inward ridge with a 0.6 mm horizontal gap (0.42 mm normal to the 45 deg faces). Both parts start on the bed, every
overhang is 45 deg, and the hub is caught both ways. The hub faces are wider than a fingertip's contact, so a pinch
touches only the hub (the rotor starts at r 11.6): that is what lets it spin. The hub stands 1.5 mm proud on top and
has a dimple on both faces.
The rays are fat at the tips: the mass out there is what keeps it spinning.

Run:  uv run --with cadquery --with trimesh --with numpy --with shapely --with matplotlib --with manifold3d \\
        --with scipy --with networkx --with rtree python claude-toys/claude_toys.py
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
T = 8.0                     # rotor thickness
R_HUB = (11.0, 7.0)         # hub radius at the faces, at the neck (z = T / 2): 45 deg cones, (11 - 7) = T / 2
GAP = 0.6                   # horizontal gap hub <-> bore
PROUD = 1.5                 # hub above the rotor's top
DIMPLE = (4.5, 1.0)         # finger dimple radius, depth
RAYS = [1.00, 0.80, 0.94, 0.78, 1.00, 0.82, 0.94, 0.78]      # 8 rays, slightly uneven like the logo
R_SPARK = 38.0


def profile(r_face, r_waist, z0, z1):
    """Section (r, z) points: r_face at z0 and z1, r_waist at the middle (45 deg cones if |r_waist - r_face| = (z1 - z0) / 2)."""
    zm = (z0 + z1) / 2
    return [(0, z0), (r_face, z0), (r_waist, zm), (r_face, z1), (0, z1)]


def hub():
    rf, rw = R_HUB
    pts = profile(rf, rw, 0, T)
    body = cq.Workplane("XZ").polyline(pts).close().revolve(360, (0, 0, 0), (0, 1, 0))
    body = body.faces("<Z").edges().chamfer(0.5)     # first layer squishes out: keep 1.1 mm to the rotor there
    body = body.union(cq.Workplane("XY").workplane(offset=T).circle(rf).extrude(PROUD))
    r, d = DIMPLE
    body = body.cut(cq.Workplane("XY").workplane(offset=T + PROUD - d).circle(r).extrude(d + 1))
    body = body.cut(cq.Workplane("XY").workplane(offset=-1).circle(r).extrude(1 + d))
    return body


def spark_outline():
    rays = []
    for k, f in enumerate(RAYS):
        L = R_SPARK * f
        tip = 6.5 if f > 0.9 else 5.0
        ray = Polygon([(0, -7.0), (L - tip, -tip), (L - tip, tip), (0, 7.0)]).union(Point(L - tip, 0).buffer(tip))
        rays.append(affinity.rotate(ray, 360 / len(RAYS) * k, origin=(0, 0)))
    return unary_union(rays + [Point(0, 0).buffer(17.0)]).buffer(1.0).buffer(-1.0).simplify(0.05)


def rotor():
    s = spark_outline()
    w = cq.Workplane("XY").polyline(list(s.exterior.coords)[:-1]).close().extrude(T)
    rf, rw = R_HUB
    bore = cq.Workplane("XZ").polyline(profile(rf + GAP, rw + GAP, -0.01, T + 0.01)).close().revolve(360, (0, 0, 0), (0, 1, 0))
    w = w.cut(bore)
    w = w.faces(">Z or <Z").edges("not %CIRCLE").chamfer(0.6)
    return w


def mesh(wp):
    path = os.path.join(HERE, "_tmp.stl")
    cq.exporters.export(wp, path)
    m = trimesh.load(path)
    os.remove(path)
    return m


def preview(h, r):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    fig = plt.figure(figsize=(12, 5))
    ax = fig.add_subplot(1, 2, 1, projection="3d")
    for m, col in ((r, (0.85, 0.47, 0.34)), (h, (0.95, 0.93, 0.88))):
        light = np.clip(m.face_normals @ np.array([0.3, -0.6, 0.75]), 0.2, 1.0)[:, None]
        ax.add_collection3d(Poly3DCollection(m.triangles, facecolors=np.array(col) * light))
    ax.set_xlim(-40, 40); ax.set_ylim(-40, 40); ax.set_zlim(-36, 44)
    ax.view_init(35, -60); ax.set_axis_off(); ax.set_title("Claude spark spinner")
    ax = fig.add_subplot(1, 2, 2)
    for m, col in ((r, "#d9785a"), (h, "#8a8578")):
        sec = m.section(plane_origin=(0, 0, 0), plane_normal=(0, 1, 0))
        for e in sec.discrete:
            ax.fill(e[:, 0], e[:, 2], color=col, alpha=0.9)
    ax.set_xlim(-20, 20); ax.set_ylim(-3, 12); ax.set_aspect("equal")
    ax.set_title("section through the hub (bed at z 0)"); ax.set_xlabel("mm")
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "preview.png"), dpi=110)


if __name__ == "__main__":
    h, r = mesh(hub()), mesh(rotor())
    for n, m in (("hub", h), ("rotor", r)):
        print(f"{n:5s} {m.extents.round(1)}  watertight={m.is_watertight}  bodies={len(m.split())}  "
              f"min z {m.bounds[0][2]:.2f}  {m.volume / 1000:.1f} cm3")
    # clearance: hub surface points to the rotor
    pts = h.sample(20000)
    d = np.abs(trimesh.proximity.signed_distance(r, pts))
    inside = trimesh.proximity.signed_distance(r, pts) > 0
    print(f"hub vs rotor: min distance {d.min():.2f} mm, hub points inside the rotor {inside.sum()}")
    # trapped: the hub's waist is wider than the bore's mouth
    print(f"capture: hub face r {R_HUB[0]} vs rotor ridge r {R_HUB[1] + GAP} -> overlap {R_HUB[0] - R_HUB[1] - GAP:.1f} mm each way")
    both = trimesh.util.concatenate([h, r])
    both.export(os.path.join(HERE, "spinner.stl"))
    preview(h, r)
