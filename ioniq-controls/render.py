"""Studio renders for controls.py: panel, stalk, stalk mechanism (lid and upper half off), exploded switch + cap."""
import os
import sys

import numpy as np
import trimesh

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "crab-arm"))
import render_v2 as R  # noqa: E402

WHITE = (0.90, 0.90, 0.89)
CAP = (0.20, 0.21, 0.23)
HOUSING = (0.10, 0.10, 0.11)
STEM = (0.95, 0.78, 0.12)
METAL = (0.75, 0.62, 0.30)
STEEL = (0.62, 0.64, 0.67)


def shift(m, d):
    m = m.copy()
    m.apply_translation(d)
    return m


def switch_items(parts):
    body, pins, stem = parts
    return [(body, HOUSING), (pins, METAL, 0.5), (stem, STEM)]


def preview(asm, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import controls as C

    panel = [(m, WHITE) for m in asm["panel"]] + [(m, CAP) for m in asm["caps"]]
    st = asm["stalk"]
    stalk = [(st["block"], WHITE), (st["lid"], WHITE), (st["upper"], WHITE), (st["lower"], WHITE),
             (st["ring"], CAP), (st["pcap"], CAP)]
    bolt = trimesh.creation.cylinder(2.5, 100.0, sections=32)
    bolt.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, (0, 1, 0)))
    x0 = C.LEVER_X[0] + 3.8
    bolt.apply_translation((x0 + 50.0, 0, C.AXIS))
    head = trimesh.creation.cylinder(4.6, 3.5, sections=6)
    head.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, (0, 1, 0)))
    head.apply_translation((x0 - 1.75, 0, C.AXIS))
    inside = [(st["block"], WHITE), (st["lower"], WHITE), (st["lever"], (0.85, 0.45, 0.20)),
              (bolt, STEEL, 0.5), (head, STEEL, 0.5)] + [(m, CAP) for m in st["cups"]]
    for sw in st["switches"][:2]:
        inside += switch_items(sw)

    # exploded: plate piece, switch, window cap
    plate = trimesh.creation.box((26, 26, 1.5))
    plate = plate.difference(trimesh.creation.box((14, 14, 4))) if hasattr(plate, "difference") else plate
    plate.apply_translation((0, 0, -0.75))
    explode = [(plate, WHITE)] + switch_items([shift(p, (0, 0, 14)) for p in asm["switch"]]) + \
        [(shift(asm["win_cap"], (0, 0, 34)), CAP)]

    views = [("console panel (7 switches)", R._cam(235, 38, 330, (0, 0, 15)), panel),
             ("drive selector: twist ring = D / R, end button = P", R._cam(230, 22, 300, (25, 0, 28)), stalk),
             ("selector inside: lever tab between the D and R switches", R._cam(205, 42, 200, (-20, 0, 30)), inside),
             ("one window switch, exploded: plate, switch, cap", R._cam(225, 22, 150, (0, 0, 22)), explode)]
    fig, axs = plt.subplots(2, 2, figsize=(16, 12))
    for ax, (title, cam, scene) in zip(axs.ravel(), views):
        ax.imshow(R.render(scene, cam, size=(1000, 720)))
        ax.set_title(title, fontsize=14, color="#444")
        ax.set_axis_off()
    fig.tight_layout()
    fig.savefig(path, dpi=80)
    plt.close(fig)
    print("render ->", path)
