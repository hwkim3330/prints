"""1:1 A4 paper template with the four camera-mount variants: lay the camera on each and pick one.
uv run --with matplotlib --with cadquery --with trimesh --with numpy python sensor-box/cam_template.py"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import box as B
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle

VARIANTS = [   # (number, M2 centre pitch, clear-housing offset up)
    (1, (34.1, 29.0), B.CLEAR_DY),   # v5: caliper reading = near-edge gap + 2.2
    (2, (33.0, 27.9), B.CLEAR_DY),   # half way
    (3, (31.9, 26.8), B.CLEAR_DY),   # reading taken as centre distance
    (4, (34.1, 29.0), 0.0),          # clear housing centred
]
W, H = 210, 297
fig = plt.figure(figsize=(W / 25.4, H / 25.4))
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, W); ax.set_ylim(0, H); ax.set_aspect("equal"); ax.axis("off")


def mount(cx, cy, n, pitch, dy):
    px, py = B.PAD[0], B.PAD[1]
    ax.add_patch(Rectangle((cx - px / 2, cy - py / 2), px, py, fill=False, lw=0.4, ls=":", ec="0.5"))
    wx, wy = B.CAM_WIN
    ax.add_patch(Rectangle((cx - wx / 2, cy - wy / 2), wx, wy, fill=False, lw=0.6, ec="#c0392b"))
    ox, oy = B.CAM_CUT
    ax.add_patch(Rectangle((cx - ox / 2, cy + dy - oy / 2), ox, oy, fill=False, lw=0.6, ec="#2471a3"))
    for sx in (-1, 1):
        for sz in (-1, 1):
            x, y = cx + sx * pitch[0] / 2, cy + sz * pitch[1] / 2
            ax.add_patch(Circle((x, y), B.M2_CLEAR / 2, fill=False, lw=0.6, ec="k"))
            ax.plot([x - 2.5, x + 2.5], [y, y], lw=0.25, c="k")
            ax.plot([x, x], [y - 2.5, y + 2.5], lw=0.25, c="k")
    ax.text(cx, cy + py / 2 + 2, f"{n}", ha="center", va="bottom", fontsize=16, weight="bold")
    ax.text(cx, cy - py / 2 - 2, f"M2 {pitch[0]} x {pitch[1]}   opening {'up %.2f' % dy if dy else 'centred'}",
            ha="center", va="top", fontsize=6.5)


for n, pitch, dy in VARIANTS:
    k = n - 1
    mount(55 + (k % 2) * 100, 205 - (k // 2) * 85, n, pitch, dy)
ax.text(105, 285, "Sensor box camera mount - 4 variants, 1:1", ha="center", fontsize=11, weight="bold")
ax.text(105, 278, "Print at 100% / actual size (not 'fit to page'); check the 100 mm bar with a ruler. Top of page = top of box.",
        ha="center", fontsize=6.5)
lines = [
    "red = pocket for the red holder   blue = opening for the clear housing   black crosses = M2 hole centres",
    "Lay the camera face-down on each: clear housing inside blue, red holder inside red, its screw holes on the crosses.",
    "Tell me the number that fits.",
]
for k, t in enumerate(lines):
    ax.text(105, 50 - k * 5, t, ha="center", fontsize=6.5)
ax.plot([55, 155], [25, 25], c="k", lw=1)
for x in (55, 155):
    ax.plot([x, x], [23, 27], c="k", lw=1)
ax.text(105, 28, "100 mm", ha="center", fontsize=7)
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "v6", "cam_template_A4.pdf")
fig.savefig(out)
fig.savefig(out.replace(".pdf", ".png"), dpi=110)
