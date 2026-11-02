# Print audit (2026-11-01)

Bambu Lab A1 (256 × 256 × 256 mm bed, 0.4 mm nozzle). Every generator in this repo was re-run, and the result was
compared with the committed STL (volume and bounding box). Then every committed part STL went through a mesh audit
(trimesh + manifold3d), in the orientation it is saved in, which is the print orientation:

- closed 2-manifold, overlapping shells, degenerate faces;
- wall thickness, measured by rays from surface points straight inwards to the opposite wall: the share of the surface
  under 0.4 mm (one line, which the slicer drops) and under 0.8 mm (two lines);
- downward faces steeper than 55° from vertical above the first layer, as total area and as the largest connected
  patch. Every `.gcode.3mf` here is sliced with **supports off**, so a large patch is a bridge or a sag;
- bed fit.

## Regeneration

| Generator | Re-run | Same as committed? |
|---|---|---|
| `ac164162/tray.py` | yes | identical |
| `t-eth-elite/tray.py` | yes | identical. It still also writes `frames.stl` and `tray_snap.stl`, which ea13c14 removed from the repo as superseded. I deleted those copies again |
| `jetson-nano/tray.py`, `jetson-nano/case.py` | yes | identical (case: 0 clearance problems) |
| `mikrobus-led/led_click.py` | yes | identical |
| `cyd/sleeve.py` | yes | identical |
| `cyd/case.py` | yes, after fetching `cyd/ref/` from witnessmenow/ESP32-Cheap-Yellow-Display | identical |
| `t-display/case.py` | yes | identical (base × cap overlap 0, 0 clashes) |
| `crab-arm/crab.py` | yes, after fetching `sensor-box/ref/U6251.STEP` (Cytron's link) | all 12 STLs identical |
| `sensor-box/box.py` | yes | v11 body, rail bar and camera test identical (0 clearance problems) |
| `sensor-box/lid.py` | yes (default `lid-v2`) | lid identical. `assembly.stl` differs only because `../ref-dl/so102/base.stl` (the arm) is not on this machine |
| `sensor-box/cam_variants.py` | yes | **differs**: it now builds from the current box (v11), so re-running it overwrites the frozen `v5/` file. Not a defect; the committed v5 file was kept |
| `lan9692-rack/*.stl` | from lan9692-ring-rack `print_plates.py` | identical |
| `lan9692-box/*.stl` | from stl-model `lan9692-evb-case/lan9692_box.py` (other repo, not re-run) | audited as committed |

The reference files (`cyd/ref/`, `sensor-box/ref/`) stay gitignored.

## Parts still to print (QUEUE rows 10–15)

| Part | Size (mm) | Manifold | Thinnest 1 % | > 55° patch, supports off | Verdict |
|---|---|---|---|---|---|
| `sensor-box/lid-v2/lid.stl` (row 10, next) | 236.3 × 209.1 × 15 | yes | 2.9 mm | 34 mm² (name engraving, 0.6 deep) | OK |
| `lan9692-rack/A,B,C,D` (row 11) | 250 × 180 × 3 | yes | 3.0 mm | none | OK. 3 mm from the bed edge on the long side, so no brim |
| `lan9692-box/lan9692_box_tray.stl` (row 12) | 233.8 × 155.7 × 37.5 | yes | 1.2 mm | none | OK |
| `lan9692-box/lan9692_box_lid.stl`, `_front`, `_rear` | 233.8 × 155.7 × 11 / 219.8 × 36.3 × 2.4 | yes | 1.0–2.4 mm | none | OK |
| `crab-arm/coupon.stl` (row 13, first) | 111.3 × 60.7 × 3 | yes, 2 shells | 0.8 mm (horn-pocket floors) | none | OK: 0.8 is two lines, and on purpose |
| `sensor-box/lid-v3/lid.stl` | 236.3 × 229.9 × 15 | yes | 2.9 mm | 975 mm² as 1.6 mm wide grooves 0.6 mm deep | OK: the grooves are short bridges |
| `crab-arm/turret.stl`, `upper_q*.stl`, `fore_f*.stl`, `dactyl.stl` | ≤ 116 × 127 | yes | 2.8–3.3 mm | none | OK |
| `crab-arm/turntable.stl` | 96 × 94.8 × 45 | yes | 3.1 mm | 311 mm²: a Ø21.5 pocket ceiling 2.2 mm above the bed | OK: a short round bridge with walls all round |
| `crab-arm/claw.stl` | 64.3 × 124 × 43.1 | yes, **59 degenerate (zero-area) faces** | 1.3 mm | 24 mm² | OK: the slicer ignores zero-area faces |
| `crab-arm/spacer_*.stl` | 50.3 / 30.1 × 11 × 11 | yes | 4.2 mm | 19 mm² (screw-hole tops) | OK |
| **`sensor-box/lid-lidar/lid.stl`** (row 14) | 236.3 × 209.1 × 15 | yes | 2.7 mm | **3530 mm²**: the Ø86 × 1.0 mm centring recess for the OS1 | **Risk**, see below |
| `sensor-box/v11/rail_bar.stl` (row 15, printed) | 248 × 30 × 8 | yes | 4.8 mm | 30 mm² | OK |

**lid-lidar, OS1 centring recess. Fixed 2026-11-02: option (b), `ring_depth` 0 plus a 1.2 × 0.6 mm guide groove at Ø86; re-sliced (PLA and PETG).** The lid prints top face down, so the Ø86 × 1 mm recess (`LIDAR['ring']`,
`ring_depth`) is a pocket in the bed face. Its ceiling is a bridge 1 mm above the bed, about 86 mm across. The Ø37 fan
vent sits in the middle of it, so the bridge has no anchor on the inside either. It is sliced with supports off, so
that ceiling will sag towards the bed. The OS1 then sits on a wavy face instead of a flat one. I did not change the
design, because the recess is what centres the sensor while the M8 slots are diagonal. Pick one before printing:
(a) a support enforcer on just that ring in Bambu Studio (tree, build plate only); the supports are 1 mm tall and come
out easily from the open recess, or (b) `ring_depth` 0 with the OS1 centred by hand on its four M8.

## Already printed or superseded (audited, no action)

| Part | Finding |
|---|---|
| `cyd/out/top.stl`, `bottom.stl` | 2–6 % of the surface is under 0.4 mm: a 0.35 mm floor pattern and thin top details. **They are in Mechaela's original case exactly the same way** (`cyd/ref/`), so they are inherited. The case was printed 2026-10-30 and does not fit the newer board anyway (QUEUE row 0) |
| `t-display/out/cap.stl` | knife edges of 0.04–0.16 mm at the four lip corners, where the R6 corner meets the rebate, and 0.1–0.3 mm slivers along the press-flap slits. The slicer drops them, which leaves a hairline at each corner. Cosmetic. If it is reprinted, leave ≥ 0.8 mm at the rebate corner (`CORNER` / rebate) |
| `jetson-nano/out/case_lid.stl` | near-zero-thickness slivers (0.0–0.06 mm) inside the four wall corners, a meshing seam of the shelled R10 corners. Not printable material, so the slicer ignores it. v2 lid not printed yet; harmless |
| `jetson-nano/out/case_base.stl` | 0.4 % under 0.4 mm (peg chamfer tips). OK |
| `sensor-box/v2`–`v6/body.stl` | 7 separate shells each (no overlap): loose inner pieces in the old versions; v7+ is one shell. Superseded |
| `sensor-box/v9/cam_test.stl` | 328 mm² bridge (the camera window). Superseded by v10/v11 |
| `a1-cable-holder/cable_holder.stl` | open mesh: a third-party preview mesh with no generator here. Bambu Studio repairs it; already sliced |
| everything else (`ac164162`, `t-eth-elite`, `jetson-nano/out/tray.stl`, `mikrobus-led`, `cyd/out/sleeve.stl`, `t-display/out/base.stl`, sensor-box v1/v7–v11, v0-compare) | manifold, one shell per part, nothing under 0.4 mm over more than 0.3 % of the surface (edge tips), no unbridgeable overhang |

## Fits worth checking on the print (nominal, from the generators)

| Joint | Nominal | Comment |
|---|---|---|
| T-ETH pillar square pin 1.9 (diagonal 2.69) in the HAT's Ø2.75 holes | 0.06 | tight: the pin lies on the bed, so layer squish sets its height. If it will not go in, `HAT_PIN_S` 1.8 |
| T-ETH board pins Ø2.2 in Ø2.5 holes, square peg 2.8 in Ø4.3 sockets | 0.3 / 0.17 per corner | sliding |
| AC164162 M2.5 self-tap Ø2.2 | — | normal pilot |
| Sensor-box lids, nut pockets | M6 10.27 / M5 8.27 across flats (+0.27) | press-in nuts, fine |
| crab-arm servo ears / horn pockets | **unmeasured servos** (crab.py header) | that is what `coupon.stl` is for: print it first |

Nothing in this repo's generators was changed by this audit.
