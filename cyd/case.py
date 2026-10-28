"""Case for the ESP32-2432S028 "Cheap Yellow Display" (2.8" ILI9341 + resistive touch), USB-C + micro-USB board.

Starts from a printed, proven design instead of guessed board data: Mechaela's CYD Slim Snap Case from
github.com/witnessmenow/ESP32-Cheap-Yellow-Display (3dModels/Mechaelas_CYD_Snap_Case), kept in ref/ (not committed).
Its port end (the short side at x = 0; its micro-USB hole at y 14..21 matches the official drawing, ref/dims.png:
PCB 50 x 86, M3 holes 42 x 78) is opened from the top edge down to the floor between the corner posts, so the
USB-C (centre), the micro-USB and the wire power connector all come out, whichever board revision it is.
A notch from the top edge: no bridge, no supports. The top (screen) part is used as it is, face down.

Run:  uv run --with trimesh --with manifold3d --with numpy --with scipy --with networkx python case.py
"""
import os

import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
REF, OUT = os.path.join(HERE, "ref"), os.path.join(HERE, "out")
os.makedirs(OUT, exist_ok=True)

FLOOR_TOP = 1.8                 # the bottom part's floor (measured from the STL)
PORT_END = (-1.0, 4.0)          # x range through the port-end wall (wall 0..~2, corner posts at x 6)
PORT_Y = (8.0, 46.0)            # between the corner posts at y 6 and 48 (case 54 wide)

bottom = trimesh.load(os.path.join(REF, "CYD Slim Snap Bottom.stl"))
bottom.apply_translation(-bottom.bounds[0])
top = trimesh.load(os.path.join(REF, "CYD Case Top.stl"))
top.apply_translation(-top.bounds[0])

h = bottom.extents[2]
cut = trimesh.creation.box(extents=(PORT_END[1] - PORT_END[0], PORT_Y[1] - PORT_Y[0], h + 2 - FLOOR_TOP))
cut.apply_translation(((PORT_END[0] + PORT_END[1]) / 2, sum(PORT_Y) / 2, FLOOR_TOP + (h + 2 - FLOOR_TOP) / 2))
bottom = trimesh.boolean.difference([bottom, cut], engine="manifold")

# the top part prints face down: its face is the z = max side in the STL
top.apply_transform(trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0]))
top.apply_translation(-top.bounds[0])

for name, m in (("bottom", bottom), ("top", top)):
    m.export(os.path.join(OUT, name + ".stl"))
    print(f"{name:7s} {m.extents.round(1)}  watertight={m.is_watertight}  {m.volume / 1000:.1f} cm3")
