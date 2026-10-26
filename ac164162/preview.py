"""Render out/tray.stl to out/preview.png (matplotlib, no GUI)."""
import os, numpy as np, trimesh, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
m = trimesh.load(os.path.join(out, "tray.stl"))
fig = plt.figure(figsize=(12, 6))
light = np.array([0.3, -0.4, 1.0]); light /= np.linalg.norm(light)
for i, (elev, azim, title) in enumerate([(40, -60, "front-left"), (35, 120, "top edge (open)")]):
    ax = fig.add_subplot(1, 2, i + 1, projection="3d")
    shade = 0.35 + 0.65 * np.clip(m.face_normals @ light, 0, 1)
    ax.add_collection3d(Poly3DCollection(m.triangles, facecolors=plt.cm.Greys(0.25 + 0.55 * shade), edgecolor="none"))
    lo, hi = m.bounds; c = (lo + hi) / 2; r = (hi - lo).max() / 2
    ax.set_xlim(c[0] - r, c[0] + r); ax.set_ylim(c[1] - r, c[1] + r); ax.set_zlim(c[2] - r, c[2] + r)
    ax.view_init(elev, azim); ax.set_axis_off(); ax.set_title(title)
plt.tight_layout(); plt.savefig(os.path.join(out, "preview.png"), dpi=90)
