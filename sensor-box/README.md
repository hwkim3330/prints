# SCOUT MINI sensor box (print version)

One-piece hexagonal box for the Bambu Lab A1, PLA, open top. One camera per face (6 cameras, 60° apart), with a Jetson AGX Orin inside. The original sheet-metal design is in [scout-mini-sensor-box](https://github.com/hwkim3330/scout-mini-sensor-box) (REV9), and its panel-assembled print version is in that repo's `rev10p/`.

![Sensor box](v10/preview.png)

3D: [v10/assembly.stl](v10/assembly.stl) · Source: [box.py](box.py) (all dimensions at the top; `VERSION` sets the output folder)

## Versions (one-piece body)

| Version | What changed | Body print | 3D |
|---|---|---|---|
| [v0-compare](v0-compare/) | Plain cups to compare shapes: round Ø245 vs hexagon (2.4 mm wall, windows only) | round 6 h 55 m / 395 g, hex 5 h 12 m / 329 g | [round](v0-compare/round.stl) · [hex](v0-compare/hex.stl) |
| [v1](v1/) | Hexagon with everything: 2.8 mm walls, corner columns, 45° floor fillet and top lip, camera pads, vents, floor holes | 9 h 02 m / 371 g (0.2 mm) | [body](v1/body.stl) |
| [v2](v2/) | 2.5 mm walls (exactly 6 lines, no gap fill), smaller columns, 0.24 mm layers | 8 h 02 m / 360 g | [body](v2/body.stl) · [assembly](v2/assembly.stl) |
| [v3](v3/) | Camera test fit the real camera; camera plate opening made square | body same as v2 | [body](v3/body.stl) · [camera plate](v3/cam_plate.stl) |
| [v4](v4/) | The clear housing is flush with the red holder's top edge (the cable is at the bottom), so the plate opening moves up 2.39 mm. The M2 holes stay symmetric on the red holder. Now the two lower holes are full circles; the two upper ones still touch the opening because they sit right beside the clear housing | body same as v2 | [camera plate](v4/cam_plate.stl) · [assembly](v4/assembly.stl) |
| [v5](v5/) | **Simpler: no camera plates.** The camera mounts straight on the wall. The clear housing goes out through an opening in the wall, the red holder sits in a 1 mm pocket inside a 4 mm pad, and 4 × M2 × 6 go from outside into the red holder. That removes 6 plates and 24 M3 screws | 7 h 57 m / 365 g | [body](v5/body.stl) · [camera test](v5/cam_test.stl) · [assembly](v5/assembly.stl) |
| [v6](v6/) | Outer corners rounded R12 instead of R3: softer look, and big round corners are less likely to lift on a 236 mm print. The corners stay about 8 mm thick thanks to the inner columns. Camera mount = v5 (variant 1, checked on paper) | 7 h 53 m / 363 g | [body](v6/body.stl) · [assembly](v6/assembly.stl) |
| [v7](v7/) | Fixes from an independent review of v6: the outer rail-bar bolt holes were buried under the 45° floor fillet (bolts now at x ±20/±60); the AGX holes sat on top of the rail bar (AGX centred, bars moved to y ±70); the lid pilot holes were sealed by the top lip; the M4 nut pocket was 7.01 mm across flats for a 7.0 mm nut (now 7.27); added a cable slot under each camera pocket, a 45° slope under the camera pads, and 4 high vents per face so it can still exhaust with a plate on top | 7 h 57 m / 360 g | [body](v7/body.stl) · [assembly](v7/assembly.stl) |
| [v8](v8/) | Ribbon channel: the camera's thin ribbon leaves between the clear housing and the red holder, which sat flat against the wall and would pinch it. An 18 mm wide, 0.8 mm deep channel now runs in the wall face under the red holder, from the opening's lower edge down to the cable slot | 8 h 02 m / 359 g | [body](v8/body.stl) · [camera test](v8/cam_test.stl) · [assembly](v8/assembly.stl) |
| [v9](v9/) | Cleaner and steadier for the 8-hour print: the low vent slots are gone (the top is open; fewer bridges and nozzle hops), a row of nine 3.5 mm round holes under the top edge of each face keeps an exhaust if a plate covers the top, a 1 mm recess outside each camera puts the M2 heads below the surface, 1 mm chamfer on the top edge. Camera mount otherwise = v8 | 7 h 19 m / 372 g (sliced file: 7 h 44 m) | [body](v9/body.stl) · [camera test](v9/cam_test.stl) · [assembly](v9/assembly.stl) |
| **[v10](v10/)** (current) | **Camera mount from the maker's CAD** (Arducam U6251 STEP, [Cytron's copy](https://drive.google.com/file/d/1SclpUZ56z3HF0iqqUI_ViT3byzcXrxU6/view), kept in `ref/` but not committed) and a clean outside. The opening follows the clear housing's rounded outline with an even 0.25 mm gap (v9: square, 0.04 mm at the bottom by the CAD), the pocket follows the red holder's outline, M2 at 34.0 x 29.0 from the CAD. The red holder's holes are 2.4 mm through, so the M2 x 6 now go in **from inside** through them into blind 1.7 mm pilots in the wall: no screw heads or recess outside. Wall in front of the camera 4.5 mm (6.9 mm of the clear housing shows). Checked against the real CAD solids on all six faces: no collisions | **7 h 44 m / 380 g** | [body](v10/body.stl) · [camera test](v10/cam_test.stl) · [assembly](v10/assembly.stl) |

Note: the M2 holes (34.1 × 29.0, symmetric on the red holder) sit right beside the clear housing. Since v4 only the upper two cut into the opening.

## Print (v10)

| File | Part | Time | PLA |
|---|---|---|---|
| `v10/cam_test.gcode.3mf` | Camera test: the wall's camera mount cut out as one small piece | 22 m | 8 g |
| `v10/body.gcode.3mf` | Body (one piece, 0.24 mm layers) | **about 7 h 44 m** | 380 g |
| `v10/rail_bars_x2.gcode.3mf` | Rail bars ×2 (after the robot arrives) | 1 h 20 m | 59 g |

- **Paper check (no printing):** [v5/cam_template_A4.pdf](v5/cam_template_A4.pdf) has the four variants below on one A4 sheet, numbered 1-4 at 1:1 (made by `cam_template.py`). Print it at 100 % (actual size), check the 100 mm bar with a ruler, and lay the camera on each one.
- **Or pick from four:** `v5/cam_test_variants.gcode.3mf` (52 min) puts four test pieces on one plate. Count the small holes in a corner to tell them apart:
  1. M2 centres 34.1 × 29.0, opening up 2.39 mm (= v5)
  2. 33.0 × 27.9, up 2.39
  3. 31.9 × 26.8 (the caliper reading taken as centre distance), up 2.39
  4. 34.1 × 29.0, opening centred

  **Result (2026-10-27): variant 1 fits (A4 check) = v5 as it is.**
- **Camera test first:** fit the real camera into it. The clear housing goes out through the opening, the red holder drops into the pocket, and 4 × M2 × 6 go in from the inside, through the red holder into the wall.
- **Body:** it takes about 8 hours, so start it in the morning and wash the bed plate first.
- **Rail bars:** print them after the robot arrives. The body doesn't depend on the rails.

## Body design

- **Size:** 240 mm across corners (fits the 256 mm bed), 208 mm across flats, 130 mm tall. The AGX (110 × 110 × 72) fits inside, checked in code.
- **Walls 2.5 mm:** exactly 6 lines of 0.42 mm (3 per side), so the slicer has no slow gap fill to do.
- **Floor 3.2 mm:** with an M3 grid every 20 mm, the AGX holes (90 × 90), and M4 holes for the rail bars.
- **Strength, all of it printable without supports:**
  - Square columns in the six inside corners, with M3 pilot holes on top for a lid or lidar plate later.
  - A 45° fillet strip all round where the walls meet the floor.
  - A 45° lip around the inside of the top rim, which stiffens it and gives a lid something to sit on.
  - 4 mm pads inside around each camera, so the M2 screws have material to bite (45° underside, cable slot below the pocket).
  - A 0.5 mm chamfer on the first layer to prevent elephant foot.
- **Vents (v9):** the top is open; a row of nine 3.5 mm round holes under the top edge of each face is the exhaust if a plate covers it.

## Camera mounting (v10, from ref/U6251.STEP)

`box.py` needs `ref/U6251.STEP` (not committed; download it from [Cytron's link](https://drive.google.com/file/d/1SclpUZ56z3HF0iqqUI_ViT3byzcXrxU6/view), product page: cytrontech.vn "Enclosure Case for Raspberry Pi Camera Module").

- **Red holder** 40.12 × 35.12, plate 3.5 thick, sits in a 1 mm pocket that follows its outline (+0.3 mm) in a 5.5 mm pad inside the wall.
- **Clear housing** 31.5 × 30.5, 11.4 above the red plate, flush with its top edge. The wall opening follows its rounded outline with an even 0.25 mm gap; the wall in front of the camera is 4.5 mm, so 6.9 mm shows outside.
- **Screws:** M2 × 6, four per camera, from inside through the red holder's 2.4 mm holes (34.0 × 29.0) into 1.7 mm blind pilots, 3 mm deep (1.5 mm of wall left outside). Mount the cameras before the AGX.
- **Ribbon:** it leaves through a 17.5 × 1.5 notch at the bottom of the clear housing, right on the red holder, into the 18 × 0.8 channel down to the cable slot. (The red holder also has a 25 × 6 slot in its back if the ribbon is routed straight into the box.)
- `box.py` reads the STEP and checks the real solids against the body on all six faces.

## Camera mounting (measured, v5)

- **Red holder** (40.16 × 35.03 × 3.51) sits in a 1 mm pocket (41 × 36) on the inside of the wall. The wall is 4 mm thick there, and 3 mm at the opening.
- **Clear housing** (31.74 × 30.25, 10.9 tall) is flush with the red holder's top edge (the cable is at the bottom). It goes out through a 32.3 × 30.8 opening that sits 2.39 mm above centre, so about 7.9 mm shows outside.
- **Screws:** M2 × 6, four per camera, from outside through the wall into the red holder. Holes at 34.1 × 29.0, symmetric on the red holder.
- The code checks the camera dummies against the body: no collisions.

## Screws (v5)

| Joint | Screw | Qty |
|---|---|---|
| Camera → body | M2 × 6 self-tapping (pan head), from inside, before the AGX goes in | 24 |
| Body ↔ rail bar | M4 × 12–16 + nut (the nuts sit in hex pockets in the bar) | 8 |
| Rail bar → robot rail | M5 + rail slider nut, rail spacing **HOLD** (closed 18 mm slots take rail spacings 206–242 mm) | 4 |
| (Later) lid → corner columns | M3 self-tapping | 6 |
