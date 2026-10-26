# prints

3D-printable parts for the Bambu Lab A1 (PLA), modelled in CadQuery.

| Part | What | Files |
|---|---|---|
| `ac164162/` | Open-top tray for the Microchip AC164162 Curiosity Nano Base for Click boards (74.93 x 107.95 mm, 6x M2.5 from the official drawing). 3.5 mm standoffs, USB/switch edge left open, slot in the right wall for the right-angle Xplained Pro header. 32 min, 24 g. | `tray.py`, `out/tray.stl`, `out/tray.gcode.3mf` |
| `ac164162/` snap | Screwless Pi-case style version: pins on the corner standoffs + four flex clips over the PCB edge. 35 min, 24 g. | `out/tray_snap.stl`, `out/tray_snap.gcode.3mf` |

Model: `uv run --with cadquery python ac164162/tray.py`
Slice for the A1 (Bambu Studio in an x86 Linux container): `bambu-cli/slice.sh ac164162/out/tray.gcode.3mf ac164162/out/tray.stl`
Print: copy the `.gcode.3mf` into the SD card's `model/` folder and pick it on the printer.

First print (8 mm standoffs) sat too high; lowered to 3.5 mm, not re-fitted yet.

## a1-cable-holder
Bambu Lab A1 cable holder by its MakerWorld author (model 119194, CC BY-NC). It snaps onto the A1 above the X axis.
https://makerworld.com/en/models/119194
The STL comes from the public preview mesh. It is sliced to match the author's profile: 3 walls, 15% infill, no supports. It takes about 39 minutes and 16 g.

## t-eth-elite
Open-top tray for the LILYGO T-ETH Elite (ESP32-S3 + W5500 + PoE). The board geometry comes from LILYGO's official 3D model. The RJ45, USB-C, BOOT/RST buttons and microSD slot are all left open.
- `out/tray_snap.gcode.3mf`: screwless. Pins go through the 4 corner holes and 4 clips hold the board. About 21 minutes, 12 g.
- `out/tray.gcode.3mf`: M2.5 self-tapping screws. About 18 minutes, 11 g. Both on 3 mm standoffs.
- `out/frames.gcode.3mf`: Pi-shaped frames that hold up the far edge of a Pi HAT stacked on the GPIO header. The legs plug into two bosses past the button edge, and the pins go into the HAT's far holes. The bridge sits 1.5 mm below the HAT, and the opening underneath keeps the buttons and microSD reachable. Three heights: 19.0, 19.5 and 20.0 mm, marked with 1, 2 and 3 holes in the bridge. They print lying flat. About 19 minutes, 7 g.
- `out/kit_pins.gcode.3mf`: clip-free tray (pins only, the board just drops on) plus the 19.5 mm frame, about 25 minutes. `out/kit_snap.gcode.3mf`: snap tray plus the 19.5 mm frame on one plate, about 27 minutes. `out/all_snap.gcode.3mf`: snap tray plus all three frames, about 39 minutes.
