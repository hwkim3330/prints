# Print queue (Bambu Lab A1)

What is waiting to be printed, in order. Tick a row when it is printed and note what came out (fit, time, grams).
Files that live in other repos are named by repo and path; copy the `.gcode.3mf` to the SD card's `model/` folder.

| # | Part | Filament | Est. time / g | Files | Status |
|---|---|---|---|---|---|
| 1 | Printer check: Benchy from the A1's own microSD | PLA (sample) | ~40 min | printer SD `Print Files` | to do |
| 2 | Car-body surface test coupon, 0.16 mm layers (roof + bonnet pieces, brim, tree supports inside) | PLA white | 2 h 38 m / 29 g | private testbed repo, `print/sd/test_01_PLA_white_panel16.gcode.3mf` | to do |
| 3 | Same coupon at 0.12 mm / outer wall 60 mm/s, to compare layer lines with #2 under low side light | PLA white | 3 h 28 m / 30 g | private testbed repo, `print/sd/test_01_PLA_white_panel12q.gcode.3mf` | after #2 |
| 4 | Glazing corner coupon: test the fit into the roof coupon's opening (0.2 mm gap by design) | PETG (smoke/clear) | 28 m / 3.9 g | private testbed repo, `print/sd/test_02_PETG_smoke_pane.gcode.3mf` | needs PETG |
| 5 | Microchip AC164162 base tray (snap version) | PLA | 35 m / 24 g | `ac164162/out/tray_snap.gcode.3mf` | printed 2026-10-27; user: no more snap versions (screw version `tray.gcode.3mf` on SD) |
| 6 | T-ETH Elite kit v2 (tray + 19.5 mm HAT pillars, one solid rectangular base) | PLA | 25 m / 15 g | `t-eth-elite/out/kit.gcode.3mf` | on SD; v1 and the frame version came loose twice |
| 7 | Robot sensor box, one-piece hexagonal body (+ 6 camera plates, rail bars after the robot arrives) | PLA, open top | body ~8 h / 365 g | `sensor-box/v5/` (panel version: `scout-mini-sensor-box/rev10p/`) | after #8 |
| 8 | Camera test for #7: one camera plate + a wall piece with the window (camera measured: red holder 40.16 x 35.03 x 3.51, clear part 31.74 x 30.25, M2 at 34.1 x 29.0) | PLA | 25 m / 14 g | `sensor-box/v5/cam_test.gcode.3mf` (13 m) | v3 test fit; v5 mounts the camera straight on the wall (no plates) |
| 9 | Full car body (decide the layer height from #2/#3 first) | PLA white | ~31 h (body) / ~63 h (all) | private testbed repo, `print/PLATES.md` | after #2-#4 |

Notes
- PETG for anything near heat (the sensor box holds a ~60 W computer) or outdoors; PLA only for desk parts and fit tests.
- The A1 has no enclosure: PETG is fine, ABS/ASA are not.
- Slicing from Linux: `bambu-cli/slice.sh` here, or the preset flattener in `scout-mini-sensor-box/tools/flatten_bambu_preset.py`
  (the CLI slicer refuses user presets whose `inherits` it cannot resolve). The A1's default plate is the Textured PEI.
