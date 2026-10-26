"""Open-top tray for the Microchip AC164162 Curiosity Nano Base for Click boards (Bambu A1, PLA, no supports).

Board (official drawing, schematics PDF p.2): 2950 x 4250 mil = 74.93 x 107.95 mm, 1.6 mm thick,
six M2.5 holes (R1.35): 125 mil from the edges at the four corners, plus two on the top edge at
450 and 1050 mil from the left. Top edge = Curiosity Nano USB end; the battery slide switch sits
in the notch at the top right, the JST-PH battery plug next to it.

The board screws onto 4 mm standoffs (M2.5 self-tapping, or 3.5 mm heat inserts with INSERT=True),
which leaves room under the board for the through-hole header pins. The top short
edge is left open so the USB cable, switch and battery plug stay reachable; the long walls stop
at the PCB top surface so Click boards and the Xplained Pro header are free.

Screwless variant (out/tray_snap.stl): Pi-case style. Pins on the four corner standoffs go through the
board's corner holes and four flex clips on the long walls snap over the PCB edge; press the board
straight down, pull a clip outwards to take it out.

Run:  uv run --with cadquery python tray.py   ->  out/tray.stl, out/tray_snap.stl
"""
import os
import cadquery as cq

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
os.makedirs(OUT, exist_ok=True)

MIL = 0.0254
BW, BH = 2950 * MIL, 4250 * MIL           # board
HOLES = [(125, 125), (450, 125), (1050, 125), (2825, 125), (125, 4125), (2825, 4125)]  # mil, from top-left
PCB_T = 1.6
CLEAR = 0.5           # gap board <-> wall
WALL = 2.0
FLOOR = 2.0
STANDOFF_H = 4.0
STANDOFF_D = 6.0
INSERT = False        # True: 3.5 mm holes for M2.5 heat inserts
HOLE_D = 3.5 if INSERT else 2.2
OPEN_TOP_EDGE = True
PIN_D = 2.3           # snap variant: pin through the 2.7 mm holes
CLIP_W = 10.0         # snap variant: flex clip width, slot either side
CLIP_SLOT = 1.0
CLIP_DEPTH = 5.6      # how far down the slots run (clip flex length)
LIP = 0.9             # how far the clip lip reaches over the PCB edge
CLIP_YS = (24.0, -40.0)  # clip centres along the long walls (clear of the finger notch)

IW, IH = BW + 2 * CLEAR, BH + 2 * CLEAR
OW, OH = IW + 2 * WALL, IH + 2 * WALL
WALL_H = FLOOR + STANDOFF_H + PCB_T       # flush with the PCB top


def tray(snap=False):
    # board coordinates: x right, y down from the top-left corner; model: centred, +Y = board top edge
    def at(xm, ym):
        return (xm * MIL - BW / 2, BH / 2 - ym * MIL)

    body = cq.Workplane("XY").box(OW, OH, WALL_H, centered=(True, True, False)).edges("|Z").fillet(3)
    cavity = (cq.Workplane("XY").workplane(offset=FLOOR).box(IW, IH, WALL_H, centered=(True, True, False))
              .edges("|Z").fillet(1.5))
    body = body.cut(cavity)
    if OPEN_TOP_EDGE:  # whole top short wall down to the standoff tops: USB, switch, battery plug
        body = body.cut(cq.Workplane("XY").workplane(offset=FLOOR + 2)
                        .center(0, OH / 2).box(IW - 6, WALL * 4, WALL_H, centered=(True, True, False)))
    # finger notches on the long walls to lift the board out
    for sx in (-1, 1):
        body = body.cut(cq.Workplane("XY").workplane(offset=FLOOR + 4)
                        .center(sx * OW / 2, -10).box(WALL * 4, 22, WALL_H, centered=(True, True, False)))
    # standoffs
    pts = [at(x, y) for x, y in HOLES]
    posts = (cq.Workplane("XY").workplane(offset=FLOOR).pushPoints(pts)
             .circle(STANDOFF_D / 2).extrude(STANDOFF_H))
    body = body.union(posts)
    if not snap:
        return body.cut(cq.Workplane("XY").workplane(offset=FLOOR + 1).pushPoints(pts)
                        .circle(HOLE_D / 2).extrude(STANDOFF_H))
    # pins on the four corner standoffs, chamfered so the board drops on easily
    corners = [at(x, y) for x, y in HOLES if x in (125, 2825)]
    pins = (cq.Workplane("XY").workplane(offset=FLOOR + STANDOFF_H).pushPoints(corners)
            .circle(PIN_D / 2).extrude(PCB_T + 0.8).faces(">Z").edges().chamfer(0.5))
    body = body.union(pins)
    top = WALL_H  # = PCB top surface
    for sx in (-1, 1):
        xin = sx * IW / 2
        for y in CLIP_YS:
            # raise the clip above the PCB, then free it with a slot each side
            body = body.union(cq.Workplane("XY").workplane(offset=top - 1)
                              .center(sx * (IW / 2 + WALL / 2), y).box(WALL, CLIP_W, 2.6, centered=(True, True, False)))
            for dy in (-1, 1):
                body = body.cut(cq.Workplane("XY").workplane(offset=top - CLIP_DEPTH)
                                .center(sx * (IW / 2 + WALL / 2), y + dy * (CLIP_W + CLIP_SLOT) / 2)
                                .box(WALL * 2, CLIP_SLOT, CLIP_DEPTH + 5, centered=(True, True, False)))
            # lip: flat underside just above the PCB, sloped top so the board pushes the clip out
            z0 = top + 0.15
            lip = (cq.Workplane("XZ").polyline([(xin, z0), (xin - sx * LIP, z0), (xin - sx * LIP, z0 + 0.3),
                                                 (xin, z0 + 1.4)]).close()
                   .extrude(CLIP_W / 2, both=True).translate((0, y, 0)))
            body = body.union(lip)
    return body


if __name__ == "__main__":
    t = tray()
    cq.exporters.export(t, os.path.join(OUT, "tray.stl"))
    cq.exporters.export(tray(snap=True), os.path.join(OUT, "tray_snap.stl"))
    print(f"tray {OW:.1f} x {OH:.1f} x {WALL_H:.1f} mm (+1.6 mm clips on the snap version)")
