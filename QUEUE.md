# Print queue (Bambu Lab A1)

What is waiting to be printed, in order. Tick a row when it is printed and note what came out (fit, time, grams).
Files that live in other repos are named by repo and path; copy the `.gcode.3mf` to the SD card's `model/` folder.

| # | Part | Filament | Est. time / g | Files | Status |
|---|---|---|---|---|---|
| 1 | Printer check: Benchy from the A1's own microSD | PLA (sample) | ~40 min | printer SD `Print Files` | to do |
| 2 | Car-body surface test coupon, 0.16 mm layers (roof + bonnet pieces, brim, tree supports inside) | PLA white | 2 h 38 m / 29 g | private testbed repo, `print/sd/test_01_PLA_white_panel16.gcode.3mf` | to do |
| 3 | Same coupon at 0.12 mm / outer wall 60 mm/s, to compare layer lines with #2 under low side light | PLA white | 3 h 28 m / 30 g | private testbed repo, `print/sd/test_01_PLA_white_panel12q.gcode.3mf` | after #2 |
| 4 | Glazing corner coupon: test the fit into the roof coupon's opening (0.2 mm gap by design) | PETG (smoke/clear) | 28 m / 3.9 g | private testbed repo, `print/sd/test_02_PETG_smoke_pane.gcode.3mf` | needs PETG |
| 5 | Microchip AC164162 base tray (snap version) | PLA | 35 m / 24 g | `ac164162/out/tray_snap.gcode.3mf` | check: refit after standoffs went 8 → 3.5 mm |
| 6 | T-ETH Elite kit (tray + 19.5 mm HAT pillars) | PLA | 22 m / 13 g | `t-eth-elite/out/kit.gcode.3mf` | check |
| 7 | Robot sensor box REV10-P (round one-piece body, lid, rail plate, camera plates) | **PETG** (+ TPU gasket) | not designed yet | public repo `scout-mini-sensor-box`, `rev10p/` (brief: `rev10p/DESIGN_BRIEF.md`) | design in progress |
| 8 | Camera plates for #7, after measuring the camera housing (W x H x D, screw pitch, M2/M2.5, lens bore) | PETG | small | `scout-mini-sensor-box/rev10p/` | waits for measurements |
| 9 | Full car body (decide the layer height from #2/#3 first) | PLA white | ~31 h (body) / ~63 h (all) | private testbed repo, `print/PLATES.md` | after #2-#4 |

Notes
- PETG for anything near heat (the sensor box holds a ~60 W computer) or outdoors; PLA only for desk parts and fit tests.
- The A1 has no enclosure: PETG is fine, ABS/ASA are not.
- Slicing from Linux: `bambu-cli/slice.sh` here, or the preset flattener in `scout-mini-sensor-box/tools/flatten_bambu_preset.py`
  (the CLI slicer refuses user presets whose `inherits` it cannot resolve). The A1's default plate is the Textured PEI.
