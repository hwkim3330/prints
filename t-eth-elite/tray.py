"""Open-top tray for the LILYGO T-ETH Elite (ESP32-S3 + W5500 + PoE) (Bambu A1, PLA, no supports).

Board geometry from LILYGO's own 3D model (LilyGO-T-ETH-Series/shell/3D/T-ETH-ELite.7z), in its
coordinates (board centred, mm): PCB 66.2 x 49.2 x 1.6, four 2.5 mm holes near the corners.
-X edge: RJ45 (overhangs the edge by 5 mm and sits 1.4 mm below the PCB), +X edge: USB-C,
+Y edge: BOOT/RST side buttons on top and the microSD slot underneath, -Y edge: GPIO header.

The board sits on 5 mm standoffs (room for the microSD socket and the RJ45 underneath); walls stop
at the PCB top surface. Snap version (out/tray_snap.stl): pins through the corner holes and four flex
clips over the PCB edge, press it in; screw version (out/tray.stl): M2.5 self-tapping into the standoffs.

Run:  uv run --with cadquery python tray.py   ->  out/tray.stl, out/tray_snap.stl
"""
import os
import cadquery as cq

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
os.makedirs(OUT, exist_ok=True)

BW, BH = 66.2, 49.2
HOLES = [(-30.12, 21.63), (30.13, 21.60), (28.23, -19.97), (-29.77, -19.97)]
PCB_T = 1.6
CLEAR = 0.5
WALL = 2.0
FLOOR = 2.0
STANDOFF_H = 5.0
STANDOFF_D = 5.0
HOLE_D = 2.2          # M2.5 self-tapping
PIN_D = 2.2           # snap variant: pin through the 2.5 mm holes
CLIP_W = 10.0
CLIP_SLOT = 1.0
CLIP_DEPTH = 6.0
LIP = 0.9
# (wall, position along it); the +X edge is taken by the USB-C and the ESP32-S3 module's antenna
CLIPS = [("-y", -12.0), ("-y", 12.0), ("+y", -18.0), ("-x", 15.0)]

IW, IH = BW + 2 * CLEAR, BH + 2 * CLEAR
OW, OH = IW + 2 * WALL, IH + 2 * WALL
PCB_Z = FLOOR + STANDOFF_H                 # PCB underside
WALL_H = PCB_Z + PCB_T                     # flush with the PCB top


def cut_box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))


def tray(snap=False):
    body = cq.Workplane("XY").box(OW, OH, WALL_H, centered=(True, True, False)).edges("|Z").fillet(3)
    body = body.cut(cq.Workplane("XY").workplane(offset=FLOOR).box(IW, IH, WALL_H, centered=(True, True, False))
                    .edges("|Z").fillet(1.5))
    big = OW  # anything that reaches through a wall
    # RJ45 (-X): jack body y -14.1..4.3, bottom 1.4 below the PCB; plug latch needs room too
    body = body.cut(cut_box(-big, -IW / 2 + 1, -16.0, 6.0, PCB_Z - 2.4, WALL_H + 1))
    # USB-C (+X): y -13.3..-4.4, room for the plug overmold
    body = body.cut(cut_box(IW / 2 - 1, big, -15.9, -1.8, PCB_Z - 2.0, WALL_H + 1))
    # +Y: BOOT/RST buttons (x 8.4..23.5) and the microSD slot underneath (x 0..15.5)
    body = body.cut(cut_box(-2.0, 26.0, IH / 2 - 1, big, FLOOR + 1.0, WALL_H + 1))
    posts = cq.Workplane("XY").workplane(offset=FLOOR).pushPoints(HOLES).circle(STANDOFF_D / 2).extrude(STANDOFF_H)
    body = body.union(posts)
    if not snap:
        return body.cut(cq.Workplane("XY").workplane(offset=FLOOR + 1).pushPoints(HOLES)
                        .circle(HOLE_D / 2).extrude(STANDOFF_H))
    pins = (cq.Workplane("XY").workplane(offset=PCB_Z).pushPoints(HOLES)
            .circle(PIN_D / 2).extrude(PCB_T + 0.8).faces(">Z").edges().chamfer(0.5))
    body = body.union(pins)
    top = WALL_H
    z0 = top + 0.15
    for wall, p in CLIPS:
        s = 1 if wall[0] == "+" else -1
        half = IH / 2 if wall[1] == "y" else IW / 2
        win, wc = s * half, s * (half + WALL / 2)
        # clip raised above the PCB, freed by a slot either side; lip with a flat underside and a ramp
        if wall[1] == "y":
            body = body.union(cq.Workplane("XY").workplane(offset=top - 1).center(p, wc)
                              .box(CLIP_W, WALL, 2.6, centered=(True, True, False)))
            for d in (-1, 1):
                body = body.cut(cq.Workplane("XY").workplane(offset=top - CLIP_DEPTH)
                                .center(p + d * (CLIP_W + CLIP_SLOT) / 2, wc)
                                .box(CLIP_SLOT, WALL * 2, CLIP_DEPTH + 5, centered=(True, True, False)))
            lip = (cq.Workplane("YZ").polyline([(win, z0), (win - s * LIP, z0), (win - s * LIP, z0 + 0.3),
                                                 (win, z0 + 1.4)]).close()
                   .extrude(CLIP_W / 2, both=True).translate((p, 0, 0)))
        else:
            body = body.union(cq.Workplane("XY").workplane(offset=top - 1).center(wc, p)
                              .box(WALL, CLIP_W, 2.6, centered=(True, True, False)))
            for d in (-1, 1):
                body = body.cut(cq.Workplane("XY").workplane(offset=top - CLIP_DEPTH)
                                .center(wc, p + d * (CLIP_W + CLIP_SLOT) / 2)
                                .box(WALL * 2, CLIP_SLOT, CLIP_DEPTH + 5, centered=(True, True, False)))
            lip = (cq.Workplane("XZ").polyline([(win, z0), (win - s * LIP, z0), (win - s * LIP, z0 + 0.3),
                                                 (win, z0 + 1.4)]).close()
                   .extrude(CLIP_W / 2, both=True).translate((0, p, 0)))
        body = body.union(lip)
    return body


if __name__ == "__main__":
    cq.exporters.export(tray(), os.path.join(OUT, "tray.stl"))
    cq.exporters.export(tray(snap=True), os.path.join(OUT, "tray_snap.stl"))
    print(f"tray {OW:.1f} x {OH:.1f} x {WALL_H:.1f} mm, PCB underside at z={PCB_Z}")
