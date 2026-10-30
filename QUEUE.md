# Print queue (Bambu Lab A1)

What is waiting to be printed, in order. Tick a row when it is printed and note what came out (fit, time, grams).
Files that live in other repos are named by repo and path; copy the `.gcode.3mf` to the SD card's `model/` folder.

| # | Part | Filament | Est. time / g | Files | Status |
|---|---|---|---|---|---|
| 0 | CYD case (top + bottom), port end opened | PLA | 43 m / 16 g | `cyd/out/case.gcode.3mf` | printed 2026-10-30 (fit, speaker room: check) |
| 1 | Printer check: Benchy from the A1's own microSD | PLA (sample) | ~40 min | printer SD `Print Files` | to do |
| 2 | Car-body surface test coupon, 0.16 mm layers (roof + bonnet pieces, brim, tree supports inside) | PLA white | 2 h 38 m / 29 g | private testbed repo, `print/sd/test_01_PLA_white_panel16.gcode.3mf` | to do |
| 3 | Same coupon at 0.12 mm / outer wall 60 mm/s, to compare layer lines with #2 under low side light | PLA white | 3 h 28 m / 30 g | private testbed repo, `print/sd/test_01_PLA_white_panel12q.gcode.3mf` | after #2 |
| 4 | Glazing corner coupon: test the fit into the roof coupon's opening (0.2 mm gap by design) | PETG (smoke/clear) | 28 m / 3.9 g | private testbed repo, `print/sd/test_02_PETG_smoke_pane.gcode.3mf` | needs PETG |
| 5 | Microchip AC164162 base tray (snap version) | PLA | 35 m / 24 g | `ac164162/out/tray_snap.gcode.3mf` | printed 2026-10-27; user: no more snap versions (screw version `tray.gcode.3mf` on SD) |
| 6 | T-ETH Elite kit v2 (tray + 19.5 mm HAT pillars, one solid rectangular base) | PLA | 25 m / 15 g | `t-eth-elite/out/kit.gcode.3mf` | on SD; v1 and the frame version came loose twice |
| 7 | Robot sensor box v10, one-piece hexagonal body (camera mount from the U6251 CAD, M2 from inside, nothing on the outer face; rail bars after the robot arrives) | PLA, open top | body ~7 h 44 m / 380 g | `sensor-box/v11/body.gcode.3mf` (panel version: `scout-mini-sensor-box/rev10p/`) | **printed, fits** (user, 2026-10-30) |
| 8 | Camera test for #7: the wall's camera mount as one piece (check the clear housing in the opening, the red holder in the pocket, M2 x 6 from inside biting into the wall, the ribbon flat in its channel) | PLA | 22 m / 8 g | `sensor-box/v10/cam_test.gcode.3mf` | skipped: the body came out fine |
| 9 | Full car body (decide the layer height from #2/#3 first) | PLA white | ~31 h (body) / ~63 h (all) | private testbed repo, `print/PLATES.md` | after #2-#4 |
| 10 | Sensor box lid "킹크랩" v2: carries an SO-ARM102 arm (4 x M6 x 25 + nuts; v1 = SO-101), 6 x M3 into the body's corner columns, 10 mm exhaust gap | PLA (PETG if it gets warm) | 3 h 01 m / 134 g | `sensor-box/lid-v2/lid.gcode.3mf` (on SD) | **next** |
| 11 | LAN9692 rack plates printed instead of acrylic, one stack: A-base, B-ecu, C-can x2, D-top (same holes as the DXF, rim under the edge, 40 % infill) | PLA | ~2 h 35 m / 137 g each, 12 h 50 m / 690 g per stack | `lan9692-rack/<plate>.gcode.3mf` (source: lan9692-ring-rack `print_plates.py`) | A-base printed 2026-10-30; B, C x2, D to do |
| 12 | LAN9692 EVB closed box, vented, 40 mm lid fan over U1 (alternative to the rack in #11 for one board): plate 1 tray, plate 2 lid + front + rear panel (panels flat). Floor and panels flat on the bed, no brim, no supports. Screws: 8 x M3x8 PCB, 4 x M3x10 lid, 4 x M3x16 + nuts fan, 4 rubber feet | PLA | tray 3 h 11 m / 86 g; lid + panels 2 h 55 m / 92 g (6 h 06 m / 178 g) | `lan9692-box/lan9692_box_tray.gcode.3mf`, `lan9692-box/lan9692_box_lid_panels.gcode.3mf` (source: stl-model `lan9692-evb-case/lan9692_box.py`) | to do |
| 13 | King Crab arm (3 x MG996R + 2 x MG90S) on lid-v3. **Print the fit coupon first** (servo ears + both horn pockets; measure the servos), then lid-v3, turret, turntable, upper arm, forearm + finger, claw. Needs PCA9685 + 6 V ≥5 A BEC + screws (list in the README) | PLA orange (lid: PETG if it gets warm) | coupon 26 m / 8 g; lid 3 h 00 m / 133 g; arm 6 h 30 m / 232 g (5 plates) | `crab-arm/coupon.gcode.3mf`, `sensor-box/lid-v3/lid.gcode.3mf`, `crab-arm/*.gcode.3mf` ([README](crab-arm/README.md)) | to do: coupon first |
| 14 | Sensor box lid "lidar" (temporary): Ouster OS1 on radial M3 slots, M5 traps for the later aluminium plate, 6 x M3 into the body | PLA | 3 h 12 m / 131 g + collar 35 m / 17 g | `sensor-box/lid-lidar/lid.gcode.3mf`, `collar.gcode.3mf` | to do (short trials only: PLA under the OS1 gets hot) |

Notes
- PETG for anything near heat (the sensor box holds a ~60 W computer) or outdoors; PLA only for desk parts and fit tests.
- The A1 has no enclosure: PETG is fine, ABS/ASA are not.
- Slicing from Linux: `bambu-cli/slice.sh` here, or the preset flattener in `scout-mini-sensor-box/tools/flatten_bambu_preset.py`
  (the CLI slicer refuses user presets whose `inherits` it cannot resolve). The A1's default plate is the Textured PEI.
