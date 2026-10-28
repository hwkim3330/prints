"""Tiny pumpkin case for the LILYGO TTGO T-Display (ESP32, 1.14" 135x240) with a 1000 mAh TW102050 cell taped
to its back (Bambu A1, PLA, no supports, no bridges, no screws, no clips).

Two parts: a base tray that holds board + battery, with a key-ring loop on the far end, and a thin cap with the
screen window and two press flaps over the board buttons; shallow grooves on the cap and the base walls are the pumpkin's ribs
(made for red-orange PLA; the face is drawn on the screen). The cap's lip slides over a tongue on the base (friction fit, like jetson-nano/case.py).

The battery's connector end makes the stack a wedge (user-measured 18.8 mm at the USB end, 13 mm at the other),
so the base floor follows it: the bottom sits flat on the desk and the screen leans ~6 degrees toward you,
with the USB-C cable leaving from the back, the key-ring loop at the other end.

Board data: LILYGO's official STEP (github.com/Xinyuan-LilyGO/TTGO-T-Display, 3d_file/T-Display.step), ref/.
Board frame: x across (0..25.16), y along (0 = USB/button end), z = 0 on the PCB's screen-side face.
The USB-C part is missing from that STEP, so its opening is generous. The active area (14.86 x 24.91) sits
somewhere inside the 17.6 x 32 glass, so the window shows the glass minus a thin edge (it is black anyway).

Run:  uv run --with cadquery --with trimesh --with manifold3d python case.py
"""
import math
import os
import cadquery as cq

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
os.makedirs(OUT, exist_ok=True)

BW, BL, PCB_T = 25.16, 51.48, 1.0
GLASS = (3.72, 10.65, 17.6, 32.0, 1.56)          # x0, y0, w, l, thickness
BUTTONS = [(4.5, 3.37), (20.98, 3.37)]            # GPIO0 / GPIO35 tact switches, 2.03 tall
FLAP = (5.4, 8.5, 0.6, 0.15)                      # press flap over each button: width, length (hinge towards the
                                                  # screen), slit, gap above the switch; thinned to ~0.7 mm so it bends
KEYRING = (10.0, 8.0, 3.0, 4.5)                   # loop on the base's far end: width, reach past the wall, thickness, hole
RESET_Y, RESET_W, RESET_TOP = 11.9, 4.6, 2.3      # side-push reset on the x = 0 edge
STACK_HI, STACK_LO = 18.8, 13.0                   # glass face -> battery back, USB end / far end (measured)

CLEAR = 0.3                                       # board to wall
CLEAR_Z = 0.8                                     # under the battery
WALL = 2.4
FLOOR = 1.6
TOP_T = 1.2
SEAM_DROP = 0.3                                   # seam just under the PCB's screen-side face
TONGUE = (1.0, 1.5)                               # thickness, height above the seam
TONGUE_CLEAR = 0.2
CORNER = 6.0                                      # round like a pumpkin; 1 mm of cap wall left at the rebate corner
POCKET_R = 0.8                                    # inner corner: square-cornered board with CLEAR
WIN = (16.0, 30.2)
USB = (13.0, -6.6, 1.0)                           # opening width, z bottom, z top (fits a plug's overmould)

IW, IL = BW + 2 * CLEAR, BL + 2 * CLEAR
OW, OL = IW + 2 * WALL, IL + 2 * WALL
SEAM = -SEAM_DROP
CEIL = GLASS[4] + 0.1                             # cap ceiling underside, rests on the glass
TOP = CEIL + TOP_T
cx, cy = BW / 2, BL / 2                           # board frame -> centred frame

# battery back plane (z at the USB end, slope along +y) and the floor under it
Z_HI = GLASS[4] - STACK_HI - CLEAR_Z
Z_LO = GLASS[4] - STACK_LO - CLEAR_Z
SLOPE = (Z_LO - Z_HI) / BL
TILT = math.degrees(math.atan(SLOPE))


def plane_z(y_c):
    """Floor-top z at centred y."""
    return Z_HI + SLOPE * (y_c + cy)


def below(z_mid):
    """Half-space under the tilted plane that passes z_mid at y = 0 (centred)."""
    return (cq.Workplane("XY").box(300, 300, 100).translate((0, 0, -50))
            .rotate((0, 0, 0), (1, 0, 0), TILT).translate((0, 0, z_mid)))


def prism(w, l, z0, z1, r):
    return cq.Workplane("XY").workplane(offset=z0).rect(w, l).extrude(z1 - z0).edges("|Z").fillet(r)


def base():
    b = prism(OW, OL, plane_z(0) - FLOOR - 5, SEAM, CORNER).cut(below(plane_z(0) - FLOOR))
    b = b.faces("<Z").edges().chamfer(0.6)
    b = b.cut(prism(IW, IL, plane_z(0) - 5, SEAM + 1, POCKET_R).cut(below(plane_z(0))))
    ring = (prism(IW + 2 * TONGUE[0], IL + 2 * TONGUE[0], SEAM - 0.01, SEAM + TONGUE[1], POCKET_R + TONGUE[0])
            .cut(prism(IW, IL, SEAM - 1, SEAM + TONGUE[1] + 1, POCKET_R)))
    ring = ring.cut(cq.Workplane("XY").box(10, 7, 10).translate((-OW / 2, RESET_Y - cy, SEAM + 2)))
    b = b.union(ring).cut(ribs_side()).union(keyring())
    w, z0, z1 = USB
    return b.cut(cq.Workplane("XY").box(w, 10, z1 + 5 - z0).translate((0, -OL / 2, (z0 + z1 + 5) / 2)))


def keyring():
    """Loop on the far end (the USB cable leaves the other end), its underside in the base's tilted bottom plane."""
    w, reach, t, d = KEYRING
    y0 = OL / 2 - WALL / 2
    lobe = (cq.Workplane("XY").workplane(offset=-40).center(0, y0 + reach / 2).rect(w, reach).extrude(60)
            .union(cq.Workplane("XY").workplane(offset=-40).center(0, OL / 2 + reach - w / 2).circle(w / 2).extrude(60)))
    lobe = lobe.cut(cq.Workplane("XY").workplane(offset=-40).center(0, OL / 2 + reach - w / 2).circle(d / 2).extrude(60))
    lobe = lobe.cut(prism(IW, IL, -40, 20, POCKET_R))   # never into the cavity
    bottom = plane_z(0) - FLOOR
    return lobe.cut(below(bottom)).intersect(below(bottom + t / math.cos(math.radians(TILT))))


RIB = (1.0, 0.45)                                 # groove width, depth


def ribs_top():
    out = None
    for x in (-(WIN[0] / 2 + 3.6), WIN[0] / 2 + 3.6):
        y0 = BUTTONS[0][1] - cy - FLAP[0] / 2 + FLAP[1] + 2.0      # stops 2 mm past the press flaps' hinges
        y1 = OL / 2 - 4.0
        g = cq.Workplane("XY").box(RIB[0], y1 - y0, 2).translate((x, (y0 + y1) / 2, TOP + 1 - RIB[1]))
        out = g if out is None else out.union(g)
    return out


def ribs_side():
    out = None
    for s in (-1, 1):
        g = (cq.Workplane("XY").box(2 * RIB[1], OL - 2 * CORNER, RIB[0]).translate((s * OW / 2, 0, -6.0))
             .rotate((0, 0, 0), (1, 0, 0), TILT))
        out = g if out is None else out.union(g)
    return out


def cap():
    c = prism(OW, OL, SEAM, TOP, CORNER)
    c = c.faces(">Z").edges().chamfer(0.6)
    rebate_w = IW + 2 * (TONGUE[0] + TONGUE_CLEAR)
    rebate_l = IL + 2 * (TONGUE[0] + TONGUE_CLEAR)
    c = c.cut(prism(rebate_w, rebate_l, SEAM - 1, SEAM + TONGUE[1] + 0.2, POCKET_R + TONGUE[0] + TONGUE_CLEAR))
    c = c.cut(prism(IW, IL, SEAM - 1, CEIL, POCKET_R))
    gx, gy = GLASS[0] + GLASS[2] / 2 - cx, GLASS[1] + GLASS[3] / 2 - cy
    win = (cq.Workplane("XY").workplane(offset=CEIL - 1).center(gx, gy).rect(*WIN).extrude(TOP - CEIL + 2)
           .edges("|Z").fillet(1.0))
    c = c.cut(win).cut(ribs_top())
    lo = cq.Sketch().rect(WIN[0] - 0.2, WIN[1] - 0.2).vertices().fillet(0.9)   # starts inside the window: no shared faces
    hi = cq.Sketch().rect(WIN[0] + 1.22, WIN[1] + 1.22).vertices().fillet(1.61)
    c = c.cut(cq.Workplane("XY").workplane(offset=TOP - 0.7).center(gx, gy)
              .placeSketch(lo, hi.moved(cq.Location(cq.Vector(0, 0, 0.71)))).loft())   # 45 deg bevel round the window
    w, ln, slit, gap = FLAP
    for x, y in BUTTONS:                             # U-shaped slit, hinge on the screen side, thinned from below
        y0 = y - cy - w / 2
        u = (cq.Workplane("XY").workplane(offset=CEIL - 1).center(x - cx, y0 - slit + (ln + slit) / 2)
             .rect(w + 2 * slit, ln + slit).extrude(TOP - CEIL + 2).edges("|Z").fillet(w / 2 + slit - 0.01)
             .cut(cq.Workplane("XY").workplane(offset=CEIL - 2).center(x - cx, y0 + (ln + 1) / 2)
                  .rect(w, ln + 1).extrude(TOP - CEIL + 4).edges("|Z").fillet(w / 2 - 0.01)))
        under = (cq.Workplane("XY").workplane(offset=CEIL - 1).center(x - cx, y0 + ln / 2).rect(w + 2 * slit, ln)
                 .extrude(2.03 + gap - CEIL + 1))
        c = c.cut(u).cut(under)
    rx0, rx1 = -OW / 2 - 1, 3.2 - cx                 # through the wall and over the switch body (to x = 3.2 on the board)
    c = c.cut(cq.Workplane("XY").box(rx1 - rx0, RESET_W + 1.0, RESET_TOP - SEAM + 1)
              .translate(((rx0 + rx1) / 2, RESET_Y - cy, (SEAM - 1 + RESET_TOP) / 2)))
    w, z0, z1 = USB
    return c.cut(cq.Workplane("XY").box(w, 10, z1 - SEAM + 1).translate((0, -OL / 2, (SEAM - 1 + z1) / 2)))


def dummies():
    """Board, glass, buttons, reset, battery connector, USB-C guess and the battery wedge, centred frame."""
    def blk(x0, y0, z0, w, l, h):
        return cq.Workplane("XY").box(w, l, h).translate((x0 + w / 2 - cx, y0 + l / 2 - cy, z0 + h / 2))
    d = {
        "pcb": blk(0, 0, -PCB_T, BW, BL, PCB_T),
        "glass": blk(GLASS[0], GLASS[1], 0, GLASS[2], GLASS[3], GLASS[4]),
        "button0": blk(3.11, 1.3, 0, 2.77, 4.14, 2.03),
        "button1": blk(19.6, 1.3, 0, 2.77, 4.14, 2.03),
        "reset": blk(0.47, 9.58, 0, 2.34, 4.59, 2.03),
        "bat_conn": blk(9.7, 6.35, -PCB_T - 3.4, 4.25, 4.2, 3.4),
        "usb_c": blk(BW / 2 - 4.5, -0.5, -PCB_T - 3.2, 9.0, 7.3, 3.2),
    }
    wedge = prism(20.0, 50.0, -40, -PCB_T - 0.01, 0.5).cut(below(plane_z(0) + CLEAR_Z))
    d["battery"] = wedge
    return d


if __name__ == "__main__":
    import trimesh
    b, c = base(), cap()

    def mesh(shape, name):
        p = os.path.join(OUT, name)
        cq.exporters.export(shape, p, tolerance=0.01, angularTolerance=0.05)
        return trimesh.load(p)

    mb, mc = mesh(b, "_base_assembled.stl"), mesh(c, "_cap_assembled.stl")
    print("watertight", mb.is_watertight, mc.is_watertight)
    bad = 0
    for name, sh in dummies().items():
        md = mesh(sh, "_d.stl")
        for pn, mp in (("base", mb), ("cap", mc)):
            v = md.intersection(mp).volume if md.bounds[0][2] < mp.bounds[1][2] else 0.0
            if v > 0.01:
                bad += 1
                print(f"  CLASH {name} x {pn}: {v:.2f} mm3")
    v = mb.intersection(mc).volume
    print(f"base x cap overlap {v:.3f} mm3")
    print(f"clashes {bad}")
    os.remove(os.path.join(OUT, "_d.stl"))

    # print orientations: base on its tilted bottom, cap face-down
    bp = b.rotate((0, 0, 0), (1, 0, 0), -TILT)
    bp = bp.translate((0, 0, -bp.val().BoundingBox().zmin))
    cp = c.rotate((0, 0, 0), (1, 0, 0), 180)
    cp = cp.translate((0, 0, -cp.val().BoundingBox().zmin))
    cq.exporters.export(bp, os.path.join(OUT, "base.stl"), tolerance=0.01, angularTolerance=0.05)
    cq.exporters.export(cp, os.path.join(OUT, "cap.stl"), tolerance=0.01, angularTolerance=0.05)
    bb = b.union(c).val().BoundingBox()
    print(f"case {bb.xlen:.1f} x {bb.ylen:.1f} mm, {Z_HI - FLOOR:.1f}..{TOP:.1f} thick at USB end "
          f"{TOP - (Z_HI - FLOOR):.1f}, far end {TOP - (Z_LO - FLOOR):.1f}, tilt {TILT:.1f} deg")
