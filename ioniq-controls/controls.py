"""IONIQ 6-style interior controls on 10 MX switches (Gateron Yellow SZH-SW033), Bambu Lab A1, PLA.

1. Console "bridge" panel, 7 switches: 4 power windows (push = down, front lip to pull), START/STOP (round cap in a
   45-degree ring), parking assist (P) and camera. 190 x 66 x 29 mm, three flat layers + 7 caps:
     base box (floor on the bed) / switch plate (1.5 mm clip-in plate, top face on the bed) / bezel (top face on the bed)
   The caps sink into the bezel: their skirts slide 6.4 mm deep in the openings and stop on the switch plate after
   3.6 mm (the switch bottoms at 4.0), so no switch ever takes the hard stop.
2. Column drive selector, 3 switches: a stalk out of a desk block. Twist the end ring up = D, down = R; push the end
   button = P. The ring turns an M5 x 100 bolt; in the block the bolt's head drives a lever whose tab sits between two
   switches, both preloaded 0.5 mm, so their own springs centre the ring (N). D/R switch at 5.4 deg, hard stop at
   11.2 deg (switch caps land on their plate). The P switch rides inside the ring, its cap is the end button.

Everything prints flat, no supports, no brim, no snap clips, no posts: screws (M3 countersunk) and captured parts.
Nothing prints in mid air: every hole that narrows going up does it at 45 degrees (cones, pyramids, V-roofed channels),
icons are V-grooves cut by a 45-degree cone (no groove floor), switch plates are thin where the clips catch and open
on the side that prints last.

Switch numbers (MX): housing 6.6 mm above the plate top, stem top 10.2, 5.0 below the plate top + 3.3 mm pins,
travel 4.0 (actuation 2.0). Stem socket: CROSS_L x CROSS_W (env, default 4.1 x 1.35), 3.4 mm deep, in a 5.6 mm tube.

Run:  uv run --with cadquery --with trimesh --with numpy --with vtk --with matplotlib --with scipy --with networkx \\
        --with manifold3d --with shapely --with rtree python ioniq-controls/controls.py
"""
import math
import os
import sys

import cadquery as cq
import manifold3d as mf
import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")

# ---------------------------------------------------------------- switch (MX / Gateron Yellow), all from the plate top
CROSS = (float(os.environ.get("CROSS_L", 4.1)), float(os.environ.get("CROSS_W", 1.35)))
HOUSING_TOP = 6.6           # top housing above the plate top
STEM_TOP = 10.2             # cross top above the plate top (3.6 mm cross)
BELOW = 5.0                 # bottom housing below the plate top
PINS = 3.3
PLATE = 1.5                 # clip-in plate thickness
CUT = 14.0                  # plate cutout
FLANGE = 15.6               # top housing footprint
STOP = 3.6                  # cap travel to its hard stop (switch bottoms at 4.0)
PRELOAD = 0.5               # stalk D/R switches pressed at rest (centring)
ACT = 2.0                   # actuation point
TUBE_D = 5.5                # stem tube round the cross socket
TUBE_BOT = HOUSING_TOP + 0.2
SOCKET = STEM_TOP - TUBE_BOT          # 3.4 mm cross depth
CEIL = HOUSING_TOP + STOP + 0.4       # cap ceiling: clears the housing at the hard stop
WALL = 1.2                  # cap skirt
GROOVE = 0.6                # icon V-groove depth (1.2 mm wide at the surface)


# ---------------------------------------------------------------- helpers
def box(x0, y0, z0, x1, y1, z1):
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))


def rrect(cx, cy, w, l, r, z0, z1):
    wp = cq.Workplane("XY").workplane(offset=z0).center(cx, cy).rect(w, l).extrude(z1 - z0)
    return wp.edges("|Z").fillet(r) if r > 0 else wp


def cyl(cx, cy, r, z0, z1):
    return cq.Workplane("XY").workplane(offset=z0).center(cx, cy).circle(r).extrude(z1 - z0)


def cone(cx, cy, r0, r1, z0, z1):
    return cq.Workplane("XY").add(cq.Solid.makeCone(r0, r1, z1 - z0, cq.Vector(cx, cy, z0), cq.Vector(0, 0, 1)))


def hexagon(cx, cy, af, z0, z1):
    return cq.Workplane("XY").workplane(offset=z0).center(cx, cy).polygon(6, af / math.cos(math.pi / 6)).extrude(z1 - z0)


def cross(z0, z1):
    L, W = CROSS
    return box(-L / 2, -W / 2, z0, L / 2, W / 2, z1).union(box(-W / 2, -L / 2, z0, W / 2, L / 2, z1))


def csk(x, y, z, down=False, r=3.4, rh=1.7):
    """90-degree countersink for an M3 flat head; opens downward from z (bed side) unless down=False flips it."""
    h = r - rh
    if down:     # head pocket on the bed face: wide at z, narrowing upward
        return cone(x, y, r, rh, z, z + h)
    return cone(x, y, rh, r, z - h, z)


def arc(cx, cy, r, a0, a1, step=0.5):
    n = max(2, int(abs(math.radians(a1 - a0)) * r / step) + 1)
    t = np.radians(np.linspace(a0, a1, n))
    return np.c_[cx + r * np.cos(t), cy + r * np.sin(t)]


def cq2tm(wp, tol=0.02):
    path = os.path.join(OUT, "_tmp.stl")
    cq.exporters.export(wp, path, tolerance=tol, angularTolerance=0.1)
    m = trimesh.load(path)
    os.remove(path)
    return m


def to_mf(m):
    return mf.Manifold(mf.Mesh(vert_properties=np.asarray(m.vertices, np.float32),
                               tri_verts=np.asarray(m.faces, np.uint32)))


def from_mf(M):
    mm = M.to_mesh()
    return trimesh.Trimesh(np.asarray(mm.vert_properties)[:, :3], np.asarray(mm.tri_verts), process=False)


def engrave(m, paths, ztop, d=GROOVE):
    """cut V-grooves along polylines into the face at z = ztop: hull of 45-degree cones, so no groove has a floor."""
    up = 1.0
    c = mf.Manifold.cylinder(d + up, 0.0, d + up, 24).translate((0, 0, ztop - d))
    parts = []
    for p in paths:
        p = np.asarray(p, float)
        if len(p) == 1:
            parts.append(c.translate((p[0][0], p[0][1], 0)))
        for a, b in zip(p[:-1], p[1:]):
            parts.append(mf.Manifold.batch_hull([c.translate((a[0], a[1], 0)), c.translate((b[0], b[1], 0))]))
    g = mf.Manifold.batch_boolean(parts, mf.OpType.Add)
    return from_mf(to_mf(m) - g)


# ---------------------------------------------------------------- icons (generic, no logos), mm, cap frame
def icon_window(outward, rear):
    """side-window glyph: forward = +y, up = outward (-x for the left windows); the slanted edge is the pillar."""
    f = np.array([(-4.5, -3.0), (4.5, -3.0), (4.5, 1.2), (1.0, 3.6), (-4.5, 3.6), (-4.5, -3.0)])   # front door
    if rear:
        f[:, 0] *= -1
    w = [np.c_[outward * f[:, 1], f[:, 0]]]
    w.append(np.c_[outward * np.array([-5.6, -5.6]), np.array([-4.5, 4.5])])                     # door line (sill)
    return w


def icon_power(r=5.2):
    return [arc(0, 0, r, 125, 415), np.array([(0, 0.6), (0, 6.6)])]


def icon_letter_p(x0, y0, h):
    b = h * 0.3
    return [np.vstack([[(x0, y0)], [(x0, y0 + h)], arc(x0 + 0.35 * h, y0 + h - b, b, 90, -90), [(x0, y0 + h - 2 * b)]])]


def icon_park():
    return icon_letter_p(-6.5, -4.5, 9.0) + [arc(-2.5, 0, 7.6, -38, 38), arc(-2.5, 0, 10.0, -36, 36)]


def icon_camera():
    w, h, r, cy = 13.0, 8.4, 1.6, -1.0
    x0, x1, y0, y1 = -w / 2, w / 2, cy - h / 2, cy + h / 2
    body = np.vstack([arc(x1 - r, y1 - r, r, 0, 90), arc(x0 + r, y1 - r, r, 90, 180), arc(x0 + r, y0 + r, r, 180, 270),
                      arc(x1 - r, y0 + r, r, 270, 360), [(x1, y1 - r)]])
    bump = np.array([(-5.0, y1), (-4.0, y1 + 1.6), (-1.0, y1 + 1.6), (0.0, y1)])
    return [body, bump, arc(0.8, cy, 2.4, 0, 360)]


# ---------------------------------------------------------------- caps (frame: z = 0 at the plate top, stem +z)
def cap_solid(outline, inner, top, skirt=STOP, chamfer=0.8):
    c = outline(skirt, top)
    if chamfer:
        c = c.faces(">Z").edges().chamfer(chamfer)
    c = c.cut(inner(skirt - 1, CEIL))
    c = c.union(cyl(0, 0, TUBE_D / 2, TUBE_BOT, CEIL + 0.3))
    return c.cut(cross(TUBE_BOT - 0.1, STEM_TOP))


BEZEL_T = 10.0              # bezel over the plate top: cap skirts slide in it
GAP = 0.4                   # cap to opening, per side
WIN = (19.0, 30.0, 4.5)     # window cap w x l, corner r
BTN = (24.0, 19.0, 5.0)     # P / camera caps
START_R = 15.0


def cap_window(outward, rear):
    w, l, r = WIN
    top = BEZEL_T + 8.0
    lip = (7.5, 2.5)        # lip reach past the front of the body is 3.5 mm, 2.5 thick

    def outline(z0, z1):     # body + a top slab that runs on past the front: the lip
        slab = rrect(0, (lip[0] - 4) / 2, w, l + lip[0] - 4, r, z1 - lip[1], z1).faces(">Z").edges().chamfer(0.8)
        return rrect(0, 0, w, l, r, z0, z1 - lip[1] + 0.01).union(slab)
    c = cap_solid(outline, lambda z0, z1: rrect(0, 0, w - 2 * WALL, l - 2 * WALL, r - WALL, z0, z1), top, chamfer=0)
    return engrave(cq2tm(c), icon_window(outward, rear), top), top


def cap_start():
    top = BEZEL_T + 4.0
    c = cap_solid(lambda z0, z1: cyl(0, 0, START_R, z0, z1), lambda z0, z1: cyl(0, 0, START_R - WALL, z0, z1), top)
    return engrave(cq2tm(c), icon_power() + [arc(0, 0, 11.8, 0, 360)], top), top


def cap_button(icon):
    w, l, r = BTN
    top = BEZEL_T + 3.5
    c = cap_solid(lambda z0, z1: rrect(0, 0, w, l, r, z0, z1),
                  lambda z0, z1: rrect(0, 0, w - 2 * WALL, l - 2 * WALL, r - WALL, z0, z1), top)
    return engrave(cq2tm(c), icon, top), top


# ---------------------------------------------------------------- console panel (assembly frame: desk z = 0)
PW, PL, PR = 190.0, 66.0, 12.0      # outline, corner radius
BASE_H = 16.0
FLOOR = 2.4
BASE_WALL = 5.0
PLATE_T = 3.0                       # switch plate: 3 mm, 1.5 mm at each switch
Z_PT = BASE_H + PLATE_T             # plate top = 19
Z_TOP = Z_PT + BEZEL_T              # bezel top = 29
RIM = 3.0                           # bezel rim round the plate
PLATE_W, PLATE_L = PW - 2 * RIM - 0.6, PL - 2 * RIM - 0.6
SKIN = 2.4                          # bezel top skin over its lightening pockets
SCREWS = [(sx * 87.0, sy * 25.5) for sx in (-1, 1) for sy in (-1, 1)] + [(0.0, 25.5), (0.0, -25.5)]

SWITCHES = [  # name, x, y, kind, mikroBUS pin
    ("START", -72.0, 0.0, "start", "MISO"),
    ("WIN_FL", -42.0, 0.0, ("win", -1, False), "AN"),
    ("WIN_FR", -18.0, 0.0, ("win", 1, False), "RST"),
    ("WIN_RL", 18.0, 0.0, ("win", -1, True), "CS"),
    ("WIN_RR", 42.0, 0.0, ("win", 1, True), "SCK"),
    ("PARK", 68.0, 11.5, "park", "MOSI"),
    ("CAM", 68.0, -11.5, "cam", "PWM"),
]
STALK_PINS = [("D", "RX"), ("R", "TX"), ("P", "INT")]


def opening(kind, x, y, grow, z0, z1):
    if kind == "start":
        return cyl(x, y, START_R + grow, z0, z1)
    if kind in ("park", "cam"):
        return rrect(x, y, BTN[0] + 2 * grow, BTN[1] + 2 * grow, BTN[2] + grow, z0, z1)
    return rrect(x, y, WIN[0] + 2 * grow, WIN[1] + 2 * grow, WIN[2] + grow, z0, z1)


def panel_base():
    b = rrect(0, 0, PW, PL, PR, 0, BASE_H).faces(">Z or <Z").edges().chamfer(0.6)
    b = b.cut(rrect(0, 0, PW - 2 * BASE_WALL, PL - 2 * BASE_WALL, PR - BASE_WALL, FLOOR, BASE_H + 1))
    for x, y in SCREWS:
        b = b.union(cyl(x, y, 4.5, FLOOR - 0.5, BASE_H))
    for x, y in SCREWS:
        b = b.cut(cyl(x, y, 1.7, -1, BASE_H + 1)).cut(csk(x, y, 0, down=True))
    # cable exit: a notch from the top of the front wall (+y, toward the dash; the plate closes it), 14 x 5
    b = b.cut(box(-7, PL / 2 - BASE_WALL - 1, BASE_H - 5, 7, PL / 2 + 1, BASE_H + 1))
    return b


def panel_plate():
    p = rrect(0, 0, PLATE_W, PLATE_L, PR - RIM, BASE_H, Z_PT)
    for _, x, y, _, _ in SWITCHES:
        p = p.cut(box(x - CUT / 2, y - CUT / 2, BASE_H - 1, x + CUT / 2, y + CUT / 2, Z_PT + 1))
        p = p.cut(rrect(x, y, 16.6, 16.6, 1.0, BASE_H - 1, Z_PT - PLATE))      # clip relief, under the plate
    for x, y in SCREWS:
        p = p.cut(cyl(x, y, 1.7, BASE_H - 1, Z_PT + 1))
    return p


def kind_of(k):
    return k if isinstance(k, str) else "win"


def panel_bezel():
    z = BASE_H
    b = rrect(0, 0, PW, PL, PR, z, Z_TOP)
    b = b.faces(">Z").edges().chamfer(1.5).faces("<Z").edges().chamfer(0.6)
    b = b.cut(rrect(0, 0, PLATE_W + 0.6, PLATE_L + 0.6, PR - RIM + 0.3, z - 1, Z_PT))      # plate nests in the rim
    # lightening pockets under the top skin, walls kept round every opening and screw
    pocket = rrect(0, 0, PLATE_W - 6, PLATE_L - 6, PR - RIM - 3, Z_PT - 0.5, Z_TOP - SKIN)
    for _, x, y, k, _ in SWITCHES:
        pocket = pocket.cut(opening(kind_of(k), x, y, GAP + 2.0, Z_PT - 1, Z_TOP))
    for x, y in SCREWS:
        pocket = pocket.cut(cyl(x, y, 4.5, Z_PT - 1, Z_TOP))
    b = b.cut(pocket)
    for _, x, y, k, _ in SWITCHES:
        b = b.cut(opening(kind_of(k), x, y, GAP, z - 1, Z_TOP + 1))
        if k == "start":      # the START ring: a 2 mm 45-degree bevel round the cap
            b = b.cut(cone(x, y, START_R + GAP, START_R + GAP + 2.6, Z_TOP - 2.0, Z_TOP + 0.6))
        else:                 # 0.5 mm 45-degree lead-in round the other openings
            b = b.cut(opening(kind_of(k), x, y, GAP + 0.48, Z_TOP - 0.49, Z_TOP + 1).faces("<Z").edges().chamfer(0.49))
    for x, y in SCREWS:
        b = b.cut(cyl(x, y, 1.3, z - 1, Z_TOP - 2.0))       # M3 pilot from below, 8 mm into the bezel
    return b


def panel_caps():
    caps = {}
    for name, x, y, k, _ in SWITCHES:
        if k == "start":
            caps[name] = cap_start()
        elif k == "park":
            caps[name] = cap_button(icon_park())
        elif k == "cam":
            caps[name] = cap_button(icon_camera())
        else:
            caps[name] = cap_window(k[1], k[2])
    return caps


# ---------------------------------------------------------------- drive-selector stalk (assembly frame)
# block x -60..0 (stalk exits at x = 0, +x), y -33..33, desk z = 0; stalk axis along x at z = AXIS
AXIS = 26.0
BX0, BY, BH = -60.0, 33.0, 51.8       # block body (lid on top, 3 mm)
LID_T = 3.0
BW_SIDE, BW_FRONT, BFLOOR = 3.0, 5.0, 3.0
R_LEVER = 16.0                        # lever: switch contact radius (above the axis)
TAB = 3.0                             # tab half width
X_SW = -18.5                          # D/R switches' x (= lever centre)
Y_PF = TAB - PRELOAD + 12.8           # plate front face |y| (cup face 12.8 above the plate)
Z_SW = AXIS + R_LEVER
LEVER_X = (-23.0, -14.0)              # lever thickness along x (front face on the stalk's nose)
STALK_L = 64.0                        # body length out of the block
SPIGOT = (12.0, 6.5)                  # stalk end spigot r, length (inside the ring)
R_ROOT, R_TIP = 11.5, 13.5
WIRE_Y = 7.5                          # P-switch wire channel / ring wire hole radius
LID_SCREWS = [(-4.0, 29.0), (-4.0, -29.0), (-56.0, 29.0), (-56.0, -29.0)]
# ring (its own frame: z = 0 at the front face, +z toward the block)
RING_R = 17.0
U_F = 11.6                            # P switch flange plane
RING_WELL = 12.8
RING_CAV = 10.0
NUT = (8.2, 5.4)                      # M5 nyloc pocket AF, depth
RING_CB = (12.2, 8.0)                 # counterbore over the spigot: r, depth
Z_CONE_END = U_F + 10.5               # wiring cavity end, then the 45-degree closing cone
Z_NUT0 = Z_CONE_END + (RING_CAV - NUT[0] / 2)
RING_LEN = Z_NUT0 + NUT[1] + RING_CB[1] - 0.1
RING_BACK_X = STALK_L + 0.3           # ring back face in the assembly
RING_FRONT_X = RING_BACK_X + RING_LEN
PCAP_R = 12.5
PCAP_STOP = U_F - (U_F + 0.8 + 7.0 - PCAP_R)     # flange-plane height where the skirt lands on the pyramid
PCAP_SKIRT = PCAP_STOP + STOP


def stalk_block():
    outer = rrect(BX0 / 2, 0, -BX0, 2 * BY, 8.0, 0, BH).faces("<Z").edges().chamfer(0.6)
    b = outer
    b = b.cut(rrect((BX0 + BW_SIDE - BW_FRONT) / 2, 0, -BX0 - BW_FRONT - BW_SIDE, 2 * (BY - BW_SIDE), 2.0,
                    BFLOOR, BH + 1))
    for x, y in LID_SCREWS:     # corner blocks in the wall corners
        x0 = -8.0 if x > -30 else BX0
        b = b.union(box(x0, 25.0 if y > 0 else -BY, BFLOOR - 0.5, x0 + 8.0, BY if y > 0 else -25.0, BH))
    for s in (-1, 1):           # switch plate walls: 4 mm, 1.5 mm where the clips catch, U-slot open at the top
        y0, y1 = sorted((s * Y_PF, s * (Y_PF + 4.0)))
        w = box(-35.0, y0, BFLOOR - 0.5, -BW_FRONT + 0.5, y1, BH)
        w = w.cut(box(X_SW - CUT / 2, y0 - 1, Z_SW - CUT / 2, X_SW + CUT / 2, y1 + 1, BH + 1))
        r0, r1 = sorted((s * (Y_PF + PLATE), s * (Y_PF + 5.0)))
        w = w.cut(box(X_SW - 8.5, r0, Z_SW - CUT / 2 - 2.0, X_SW + 8.5, r1, BH + 1))
        b = b.union(w)
    b = b.intersect(outer)      # the corner blocks stay inside the rounded corners
    # stalk tenon slot in the front wall (lid plug closes it), cable notch in the back wall
    b = b.cut(box(-BW_FRONT - 0.1, -10.15, AXIS - 10.0, 0.1, 10.15, BH + 1))
    b = b.cut(box(BX0 - 1, -7.0, BH - 7.0, BX0 + BW_SIDE + 1, 7.0, BH + 1))
    for x, y in LID_SCREWS:
        b = b.cut(cyl(x, y, 1.3, BH - 12.0, BH + 1))
    return b


def stalk_lid():
    z0, z1 = BH, BH + LID_T
    l = rrect(BX0 / 2, 0, -BX0, 2 * BY, 8.0, z0, z1).faces(">Z").edges().chamfer(0.8)
    l = l.union(box(-BW_FRONT + 0.05, -10.05, AXIS + 10.0, -0.05, 10.05, z0 + 0.01))         # tenon slot plug
    for s in (-1, 1):            # pads on the D/R switches (bottom housing top), inside the plate slot and behind it
        y0, y1 = sorted((s * (Y_PF + 0.1), s * (Y_PF + 4.9)))
        l = l.union(box(X_SW - CUT / 2 + 0.1, y0, Z_SW + CUT / 2 + 0.05, X_SW + CUT / 2 - 0.1, y1, z0 + 0.01))
    for x, y in LID_SCREWS:
        l = l.cut(cyl(x, y, 1.7, z0 - 1, z1 + 1)).cut(csk(x, y, z1))
    return l


def stalk_half(upper):
    """one half of the stalk (split on the axis plane), assembly frame with the axis at z = 0."""
    prof = [(0, 0), (0, R_ROOT), (STALK_L, R_TIP), (STALK_L, SPIGOT[0]), (STALK_L + SPIGOT[1] - 0.6, SPIGOT[0]),
            (STALK_L + SPIGOT[1], SPIGOT[0] - 0.6), (STALK_L + SPIGOT[1], 0)]
    s = cq.Workplane("XY").polyline(prof).close().revolve(360, (0, 0, 0), (1, 0, 0))
    s = s.union(box(-BW_FRONT, -10.0, -10.0, 0.5, 10.0, 10.0))           # tenon, through the front wall
    s = s.union(box(-8.5, -14.0, -14.0, -BW_FRONT, 14.0, 14.0))          # flange inside the block
    s = s.union(cq.Workplane("YZ").workplane(offset=LEVER_X[1]).circle(6.0).extrude(-8.5 - LEVER_X[1]))  # nose
    sgn = 1 if upper else -1
    s = s.intersect(box(-20, -20, 0, 80, 20, 20) if upper else box(-20, -20, -20, 80, 20, 0))

    def channel(yc, hw, h, x0):          # groove in the split face, roofed at 45 degrees
        pts = [(yc - hw, 0), (yc + hw, 0), (yc + hw, h), (yc, h + hw), (yc - hw, h)]
        pts = [(y, sgn * z) for y, z in pts]
        return cq.Workplane("YZ").workplane(offset=x0).polyline(pts).close().extrude(STALK_L + SPIGOT[1] + 1 - x0)
    s = s.cut(channel(0.0, 2.7, 1.0, LEVER_X[1] - 1)).cut(channel(WIRE_Y, 1.5, 1.2, -8.6))
    # one M3 x 16 countersunk screw mid-length, from below
    x, y = 32.0, -6.5
    if upper:
        s = s.cut(cyl(x, y, 1.3, -0.1, 6.0)).cut(cone(x, y, 1.3, 0.05, 6.0, 7.25))
    else:
        s = s.cut(cyl(x, y, 1.7, -8.0, 0.1)).cut(cone(x, y, 3.4, 1.7, -9.3, -7.6)).cut(cyl(x, y, 3.4, -20, -9.3))
    return s


def ring():
    """the twist ring in its own frame (z = 0 front face on the bed, axis = z), wire hole on +x."""
    prof = [(0, 0), (RING_R - 1.0, 0), (RING_R, 1.0), (RING_R, 27.0), (RING_R - 2.5, RING_LEN), (0, RING_LEN)]
    r = cq.Workplane("XZ").polyline(prof).close().revolve(360, (0, 0, 0), (0, 1, 0))
    fl = None
    for i in range(30):          # grip flutes, run out through the taper at the back
        a = 2 * math.pi * i / 30
        f = cyl((RING_R + 0.4) * math.cos(a), (RING_R + 0.4) * math.sin(a), 1.0, 3.0, RING_LEN + 1)
        fl = f if fl is None else fl.union(f)
    r = r.cut(fl)
    v = cyl(0, 0, RING_WELL, -1, U_F - 5.5)                                      # cap well
    v = v.union(cone(0, 0, RING_WELL + 0.5, RING_WELL, -0.01, 0.5))
    pyr = (cq.Workplane("XY").workplane(offset=U_F - 5.5).rect(2 * (7.8 + 5.5), 2 * (7.8 + 5.5))
           .workplane(offset=6.3).rect(14.0, 14.0).loft())                      # 45-degree seat for the flange
    v = v.union(pyr.intersect(cyl(0, 0, RING_WELL, U_F - 5.6, U_F + 1.0)))
    v = v.union(box(-7, -7, U_F + 0.7, 7, 7, U_F + PLATE + 0.01))                 # 14 x 14, the clips catch behind
    v = v.union(cyl(0, 0, RING_CAV, U_F + PLATE, Z_CONE_END))                    # pins + wires
    v = v.union(cone(0, 0, RING_CAV, NUT[0] / 2, Z_CONE_END, Z_NUT0))           # 45-degree roof
    v = v.union(hexagon(0, 0, NUT[0], Z_NUT0, Z_NUT0 + NUT[1]))                 # M5 nyloc
    v = v.union(cyl(0, 0, RING_CB[0], Z_NUT0 + NUT[1], RING_LEN + 1))           # over the stalk spigot
    v = v.union(cyl(WIRE_Y, 0, 1.3, U_F + PLATE, RING_LEN + 1))                 # P-switch wires
    return r.cut(v)


def pcap():
    """end button (P), frame: z = 0 at the P switch flange plane."""
    top = U_F + 1.0
    c = cap_solid(lambda z0, z1: cyl(0, 0, PCAP_R, z0, z1), lambda z0, z1: cyl(0, 0, PCAP_R - WALL, z0, z1), top,
                  skirt=PCAP_SKIRT, chamfer=0.6)
    return engrave(cq2tm(c), icon_letter_p(-2.6, -4.5, 9.0), top)


def cup():
    """the D/R switches' caps: the lever tab presses their flat faces."""
    c = cap_solid(lambda z0, z1: rrect(0, 0, 18.6, 18.6, 1.5, z0, z1),
                  lambda z0, z1: rrect(0, 0, 16.2, 16.2, 0.5, z0, z1), 12.8, chamfer=0.5)
    return cq2tm(c)


def lever():
    """own frame = print frame: front face z = 0 on the bed (bears on the stalk nose), tab toward +y."""
    t = LEVER_X[1] - LEVER_X[0]
    p = (cq.Workplane("XY").circle(6.6).extrude(t)
         .union(box(-TAB, 0, 0, TAB, R_LEVER + 1.0, t))
         .union(cyl(0, R_LEVER + 1.0, TAB, 0, t)))
    p = p.faces("<Z").edges().chamfer(0.4)
    p = p.cut(cyl(0, 0, 2.75, -1, t + 1)).cut(hexagon(0, 0, 8.2, t - 3.8, t + 1))
    return p


def tester():
    """stem-fit tester: 4 sockets, 1..4 dots; the one that grips like a keycap sets CROSS_L/CROSS_W."""
    global CROSS
    sizes = [(4.0, 1.25), (4.05, 1.30), (4.1, 1.35), (4.15, 1.40)]
    t = rrect(0, 0, 58, 16, 3.0, 0, 2.0).faces("<Z").edges().chamfer(0.4)
    keep = CROSS
    for i, s in enumerate(sizes):
        x = -19.5 + 13 * i
        CROSS = s
        t = t.union(cyl(x, -2.0, TUBE_D / 2, 0, 2.0 + 3.8)).cut(cross(2.4, 7).translate((x, -2.0, 0)))
    CROSS = keep
    m = cq2tm(t)
    return engrave(m, [[(-19.5 + 13 * i + 1.6 * (k - i / 2), 5.0)] for i in range(4) for k in range(i + 1)], 2.0, 0.5),\
        sizes


# ---------------------------------------------------------------- switch dummy (renders only), z = 0 plate top
def switch_dummy():
    bot = box(-6.95, -6.95, -BELOW, 6.95, 6.95, 0)
    top = (cq.Workplane("XY").rect(FLANGE, FLANGE).workplane(offset=1.0).rect(FLANGE, FLANGE).loft()
           .union(cq.Workplane("XY").workplane(offset=1.0).rect(FLANGE, FLANGE).workplane(offset=5.6).rect(11, 12)
                  .loft()))
    pins = cyl(-3.81, 2.54, 0.75, -BELOW - PINS, -BELOW).union(cyl(2.54, 5.08, 0.75, -BELOW - PINS, -BELOW))
    pins = pins.union(cyl(0, 0, 2.0, -BELOW - 3, -BELOW))
    stem = box(-2.8, -2.8, HOUSING_TOP - 0.6, 2.8, 2.8, HOUSING_TOP).union(cross(HOUSING_TOP, STEM_TOP))
    return cq2tm(bot.union(top)), cq2tm(pins), cq2tm(stem)


# ---------------------------------------------------------------- frames
def T(rot=None, t=(0, 0, 0)):
    M = np.eye(4)
    if rot is not None:
        M[:3, :3] = np.array(rot, float).T      # columns = images of the local x, y, z
    M[:3, 3] = t
    return M


FLIP = T([(1, 0, 0), (0, -1, 0), (0, 0, -1)])
RING_T = T([(0, 1, 0), (0, 0, -1), (-1, 0, 0)], (RING_FRONT_X, 0, AXIS))      # local x->+y, y->-z, z->-x
PCAP_T = T([(0, 1, 0), (0, 0, 1), (1, 0, 0)], (RING_FRONT_X - U_F, 0, AXIS))  # local z -> +x (cap faces the tip)
LEVER_T = T([(0, -1, 0), (0, 0, 1), (-1, 0, 0)], (LEVER_X[1], 0, AXIS))
CUP_T = {s: T([(1, 0, 0), (0, 0, s), (0, -s, 0)], (X_SW, s * Y_PF, Z_SW)) for s in (1, -1)}


def placed(m, M):
    m = m.copy()
    m.apply_transform(M)
    return m


def on_bed(m, M=None):
    m = m.copy()
    if M is not None:
        m.apply_transform(M)
    b = m.bounds
    m.apply_translation((-(b[0][0] + b[1][0]) / 2, -(b[0][1] + b[1][1]) / 2, -b[0][2]))
    return m


def ceilings(m):
    """flat downward faces above the first 0.3 mm (normal z < -0.98), mm2, and the largest single patch."""
    z0 = m.bounds[0][2]
    c, n, a = m.triangles_center, m.face_normals, m.area_faces
    f = (n[:, 2] < -0.98) & (c[:, 2] > z0 + 0.3)
    return float(a[f].sum()), (float(c[f][:, 2].max() - z0) if f.any() else 0.0)


def save(m, name, report):
    path = os.path.join(OUT, name + ".stl")
    m.export(path)
    area, zmax = ceilings(m)
    report.append((name, m.extents.round(1), m.is_watertight, len(m.split(only_watertight=False)), area))
    print(f"{name:14s} {m.extents.round(1)}  watertight={m.is_watertight}  ceiling={area:.1f} mm2"
          + (f" (highest z {zmax:.1f})" if area else ""))
    return path


def main():
    os.makedirs(OUT, exist_ok=True)
    rep = []
    print(f"cross {CROSS[0]} x {CROSS[1]}, socket {SOCKET:.1f} deep; P cap skirt {PCAP_SKIRT:.2f} over the flange; "
          f"ring {RING_LEN:.1f} long, front at x {RING_FRONT_X:.1f}; bolt head face x {LEVER_X[0] + 3.8:.1f} -> "
          f"M5 x 100 tip at x {LEVER_X[0] + 3.8 + 100:.1f} (nut {RING_FRONT_X - Z_NUT0 - NUT[1]:.1f}.."
          f"{RING_FRONT_X - Z_NUT0:.1f})")
    act = math.degrees(math.asin((ACT - PRELOAD) / R_LEVER))
    stop = math.degrees(math.asin((STOP - PRELOAD) / R_LEVER))
    print(f"stalk twist: D/R at {act:.1f} deg, hard stop {stop:.1f} deg")

    tm, sizes = tester()
    save(on_bed(tm), "stem_tester", rep)

    asm = {}
    base, plate, bezel = cq2tm(panel_base()), cq2tm(panel_plate()), cq2tm(panel_bezel())
    save(on_bed(base), "panel_base", rep)
    save(on_bed(plate, FLIP), "panel_plate", rep)
    save(on_bed(bezel, FLIP), "panel_bezel", rep)
    asm["panel"] = [base, plate, bezel]
    caps = panel_caps()
    asm["caps"] = []
    for name, x, y, k, _ in SWITCHES:
        m, top = caps[name]
        save(on_bed(m, FLIP), "cap_" + name.lower(), rep)
        asm["caps"].append(placed(m, T(t=(x, y, Z_PT))))

    blk, lid = cq2tm(stalk_block()), cq2tm(stalk_lid())
    up, lo = cq2tm(stalk_half(True)), cq2tm(stalk_half(False))
    rg, pc, cp, lv = cq2tm(ring()), pcap(), cup(), cq2tm(lever())
    save(on_bed(blk), "stalk_block", rep)
    save(on_bed(lid, FLIP), "stalk_lid", rep)
    save(on_bed(up), "stalk_upper", rep)
    save(on_bed(lo, FLIP), "stalk_lower", rep)
    save(on_bed(rg), "stalk_ring", rep)
    save(on_bed(pc, FLIP), "stalk_pcap", rep)
    save(on_bed(cp, FLIP), "stalk_cup", rep)
    save(on_bed(lv), "stalk_lever", rep)
    asm["stalk"] = dict(block=blk, lid=lid, upper=placed(up, T(t=(0, 0, AXIS))), lower=placed(lo, T(t=(0, 0, AXIS))),
                        ring=placed(rg, RING_T), pcap=placed(pc, PCAP_T), lever=placed(lv, LEVER_T),
                        cups=[placed(cp, CUP_T[s]) for s in (1, -1)])
    sw = switch_dummy()
    asm["switch"] = sw
    asm["stalk"]["switches"] = [[placed(p, CUP_T[s]) for p in sw] for s in (1, -1)] + \
        [[placed(p, PCAP_T) for p in sw]]
    asm["panel_switches"] = [[placed(p, T(t=(x, y, Z_PT))) for p in sw] for _, x, y, _, _ in SWITCHES]
    asm["win_cap"] = caps["WIN_FL"][0]
    return asm, rep, sizes


if __name__ == "__main__":
    asm, rep, sizes = main()
    if "--no-render" not in sys.argv:
        import render
        render.preview(asm, os.path.join(HERE, "preview.png"))
