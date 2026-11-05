"""Pedal deck in millimeters. pip install manifold3d trimesh numpy matplotlib."""
from pathlib import Path
import numpy as np
import trimesh
from manifold3d import CrossSection as CS, Manifold as M

OUT = Path(__file__).resolve().parent
SERVO_LENGTH, SERVO_WIDTH = 40.7, 19.7
EAR_PITCH, EAR_WIDTH_PITCH = 49.5, 10
SERVO_Y, SERVO_Z = 10, 34
HINGE_Y, HINGE_Z = -64, 17
CARRIER_FACE = 47
COVER_FIXINGS = ((-30,-16), (30,-16), (-35,61), (35,61))

def box(w, d, h, x=0, y=0, z=0):
    return M.cube((w, d, h)).translate((x-w/2, y-d/2, z))

def rounded(w, d, h, r, x=0, y=0, z=0):
    profile = CS.square((w-2*r, d-2*r), True).offset(r, circular_segments=48)
    return profile.extrude(h).translate((x, y, z))

def bore(r, length, x, y, z, horizontal=False):
    cutter = M.cylinder(length, r, circular_segments=32)
    if horizontal:
        cutter = cutter.rotate((0, 90, 0))
    return cutter.translate((x, y, z))

def carrier(coupon=False):
    # Local axes are length, height, and outward from the case.
    plate = rounded(61 if coupon else 82, 30 if coupon else 42, 4, 3,
                    y=34 if coupon else 28)
    window = box(SERVO_LENGTH+0.8, SERVO_WIDTH+0.8, 6, 0, SERVO_Z, -1)
    plate -= window
    for x in (-EAR_PITCH/2, EAR_PITCH/2):
        for y in (SERVO_Z-EAR_WIDTH_PITCH/2, SERVO_Z+EAR_WIDTH_PITCH/2):
            plate -= bore(1.7, 6, x, y, -1)
    if not coupon:
        for x in (-35, 35):
            plate -= bore(1.7, 6, x, 15, -1)
    return plate

def assembled_carrier(side):
    right = carrier().transform(((0,0,1,CARRIER_FACE-4), (1,0,0,SERVO_Y), (0,1,0,0)))
    return right if side == 1 else right.mirror((1,0,0))

def base():
    deck = rounded(178, 156, 4.2, 14, y=-3)
    rim = (rounded(178, 156, .12, 14, y=-3, z=4.1) +
           rounded(176, 154, .12, 13, y=-3, z=4.88)).hull()
    deck += rim
    for side in (-1, 1):
        for y in (SERVO_Y-35, SERVO_Y+35):
            deck += rounded(9, 10, 15, 2, side*38.5, y, 4)
            deck -= bore(1.7, 14, side*38.5-7, y, 15, True)
        for x in (49, 81):
            deck += rounded(5, 12, 18, 2, side*x, HINGE_Y, 4)
            deck -= bore(1.7, 7, side*x-3.5, HINGE_Y, HINGE_Z, True)
        # Pedal travel ends on the base, outside the servo link plane.
        stop = rounded(9, 10, 14, 2.5, side*72, -42, 4.5)
        contact_plane = box(20, 90, 20, side*72, -44, 20)
        contact_plane = contact_plane.translate((0, -HINGE_Y, -HINGE_Z))
        contact_plane = contact_plane.rotate((-12, 0, 0)).translate((0, HINGE_Y, HINGE_Z))
        deck += stop - contact_plane
    for x, y in COVER_FIXINGS:
        deck -= bore(1.3, 7, x, y, -1)
    for x in (-69, 69):
        for y in (-62, 56):
            deck -= bore(6, 1.0, x, y, -0.4)
    # Tie the signal and power loom away from the rotating sides.
    for x in (-14, 14):
        bridge = rounded(10, 10, 5, 2, x, 55, 4)
        bridge -= bore(1.7, 12, x-6, 55, 7, True)
        deck += bridge
    return deck

def pedal(brake):
    # Assembled in right-hand coordinates, mirrored for the left.
    w = 24 if not brake else 26
    pad = rounded(w, 43, 5, 6, 65, -52, 20)
    # A hinge barrel centered on the M3 pin. A web joins it to the pad.
    pad += bore(4, 26, 52, HINGE_Y, HINGE_Z, True)
    pad += box(26, 8, 8, 65, HINGE_Y, 13)
    pad -= bore(1.7, 28, 51, HINGE_Y, HINGE_Z, True)
    # Link clevis single lug in the approximate horn plane.
    pad += rounded(4, 10, 8, 1.5, 63, -36, 15)
    pad -= bore(1.25, 6, 60, -36, 18, True)
    for y in ((-58, -51, -44) if brake else (-55, -47)):
        pad -= rounded(w-4, 1.4, 0.7, .6, 65, y, 24.5)
    return pad.mirror((1,0,0)) if brake else pad

def cover():
    # The full-width lid covers both servo horns. Front ports let only
    # the two pushrods emerge, and remain open at the print-side top.
    shell = rounded(154, 93, 49, 12, y=22, z=5)
    shell -= rounded(148, 87, 47, 9, y=22, z=4)
    for side in (-1, 1):
        shell -= rounded(44, 23, 47, 4, side*53, -22, 4)
    shell -= rounded(24, 12, 17, 4, 0, 67, 4)
    for x, y in COVER_FIXINGS:
        shell += bore(4.2, 48.9, x, y, 5)
        shell -= bore(1.7, 51, x, y, 4)
        shell -= bore(3.1, 48, x, y, 8)
    return shell

def display_dock():
    dock = rounded(33, 33, 6, 5)
    dock -= rounded(25, 25, 6, 1, z=1.6)
    dock -= box(17, 9, 6, 0, 14, 1.2)  # USB-C
    dock -= box(13, 9, 6, 0, -14, 1.2) # Grove lead
    for side in (-1, 1):
        dock -= box(8, 10, 6, side*14, 0, 1.6)  # side button access
    return dock

def link():
    rod = rounded(7.5, 41, 2.8, 3.5, y=15)
    for y in (0, 26, 29.5, 33):
        rod -= bore(1.2, 5, 0, y, -1)
    return rod

def mesh(shape):
    data = shape.to_mesh()
    return trimesh.Trimesh(data.vert_properties[:, :3], data.tri_verts, process=True)

def bed(shape):
    lo = shape.bounding_box()
    return shape.translate((0, 0, -lo[2]))

def build():
    return {
        "01-fit-check": carrier(True), "02-base": base(),
        "03-servo-carrier-x2": carrier(), "04-brake": bed(pedal(True).rotate((180,0,0))),
        "05-accel": bed(pedal(False).rotate((180,0,0))), "06-cover": bed(cover().rotate((180,0,0))),
        "07-atom-dock": display_dock(), "08-link-x2": link(),
    }

if __name__ == "__main__":
    for name, shape in build().items():
        part = mesh(shape)
        assert part.is_watertight and part.is_volume, name
        assert len(shape.decompose()) == 1, name
        assert np.all(part.extents < (256,256,256)), name
        part.export(OUT / f"{name}.stl")
        print(name, np.round(part.extents, 1), round(part.volume/1000,1))
