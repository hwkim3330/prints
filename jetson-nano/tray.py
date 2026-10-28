"""Open-top tray for the Jetson Nano Developer Kit (B01 / A02 carrier, 100 x 80 mm) (Bambu A1, PLA, no supports).

The heatsink and fan stay as they are and everything above the PCB is open: the fan's air, the ports on
the front edge, the camera connectors, the 40-pin header, the microSD slot under the heatsink and the
button header all stay reachable. The board drops onto four square pegs through its 3 mm corner holes
(no screws, no clips) and the walls stop just under the PCB top, so it can't slide.

Board data: SBC Model Framework (hominoids/SBC_Model_Framework, "jetsonnano", hand-measured PCB),
board corner at (0, 0), ports along y = 0. Holes (4,17) (90,17) (4,75) (90,75) = 86 x 58 mm pattern,
which matches NVIDIA's 86.14 x 58.25.

Run:  uv run --with cadquery python tray.py   ->  out/tray.stl
"""
import os
import cadquery as cq

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
os.makedirs(OUT, exist_ok=True)

BW, BH = 100.0, 80.0
BOARD_R = 1.4                   # pocket corner: fits a square-cornered board with CLEAR
HOLES = [(x - BW / 2, y - BH / 2) for x, y in [(4, 17), (90, 17), (4, 75), (90, 75)]]
PCB_T = 1.6
CLEAR = 0.6                     # board to wall, each side
WALL = 2.52                     # 6 lines of 0.42
FLOOR = 2.0
STANDOFF_H = 5.0                # floor top -> PCB underside (through-hole pins stick out ~2 mm)
STANDOFF_S = 7.0                # square standoff
PEG_S = 1.95                    # square peg, 2.76 mm diagonal in the 3 mm hole
PEG_L = 2.4                     # past the PCB top by 0.8 mm
WALL_DROP = 0.3                 # wall top just under the PCB top, so nothing on the edge can sit on it
CORNER = 6.0
VENTS = [(-30.0 + 12.0 * i, 0.0) for i in range(6)]   # floor slots under the board
VENT = (40.0, 5.0)

IW, ID = BW + 2 * CLEAR, BH + 2 * CLEAR
OW, OD = IW + 2 * WALL, ID + 2 * WALL
PCB_Z = FLOOR + STANDOFF_H
H = PCB_Z + PCB_T - WALL_DROP


def tray():
    t = (cq.Workplane("XY").rect(OW, OD).extrude(H).edges("|Z").fillet(CORNER)
         .faces("<Z").edges().chamfer(0.6).faces(">Z").edges().fillet(0.8))
    t = t.cut(cq.Workplane("XY").workplane(offset=FLOOR).rect(IW, ID).extrude(H).edges("|Z").fillet(BOARD_R + CLEAR))
    t = t.union(cq.Workplane("XY").workplane(offset=FLOOR - 0.01).pushPoints(HOLES)
                .rect(STANDOFF_S, STANDOFF_S).extrude(STANDOFF_H + 0.01).edges("|Z").fillet(1.0))
    t = t.union(cq.Workplane("XY").workplane(offset=PCB_Z - 0.01).pushPoints(HOLES)
                .rect(PEG_S, PEG_S).extrude(PEG_L + 0.01).faces(">Z").edges().chamfer(0.4))
    return t.cut(cq.Workplane("XY").workplane(offset=-1).pushPoints(VENTS)
                 .slot2D(VENT[0], VENT[1], 90).extrude(FLOOR + 2))


if __name__ == "__main__":
    t = tray()
    cq.exporters.export(t, os.path.join(OUT, "tray.stl"))
    bb = t.val().BoundingBox()
    print(f"tray {bb.xlen:.1f} x {bb.ylen:.1f} x {bb.zlen:.1f} mm, PCB underside at z = {PCB_Z}")
