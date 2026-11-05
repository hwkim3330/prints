"""MG996R six-arm horn adapter, dimensions in mm."""
from pathlib import Path
from math import cos, sin, radians
from manifold3d import Manifold as M, CrossSection as C
import trimesh

OUT = Path(__file__).resolve().parent
HORN_DIAMETER = 32
ARM_WIDTH = 7.32
TIP_WIDTH = 4.6
VALLEY_RADIUS = 8.1  # Paper option 01; assumed 3 mm bore, near edge.
SHOULDER_RADIUS = 8.8
ARM_THICKNESS = 2
FIT_CLEARANCE = 0.3  # Per mating side.
HORN_INNER = 6.5
HORN_OUTER = 14.5
DRUM_RADIUS = 15
BOLT_CIRCLE = 20
ANCHOR_RADIUS = 16.3

def disc(r, h, z=0):
    return M.cylinder(h, r, circular_segments=96).translate((0,0,z))

def hole(r, h, angle, radius, z=-1):
    a = radians(angle)
    return disc(r,h,z).translate((radius*cos(a),radius*sin(a),0))

def horn_pocket():
    radius = HORN_DIAMETER / 2
    tip_radius = TIP_WIDTH / 2
    tip_center = radius - tip_radius
    valley_x = VALLEY_RADIUS * cos(radians(30))
    valley_y = VALLEY_RADIUS * sin(radians(30))
    arm = [(valley_x, -valley_y), (SHOULDER_RADIUS, -ARM_WIDTH / 2)]
    for angle in range(-90, 91, 5):
        t = radians(angle)
        arm.append((tip_center + tip_radius*cos(t), tip_radius*sin(t)))
    arm.append((SHOULDER_RADIUS, ARM_WIDTH / 2))

    outline = []
    for angle in range(0, 360, 60):
        t = radians(angle)
        outline.extend((x*cos(t)-y*sin(t), x*sin(t)+y*cos(t)) for x,y in arm)
    pocket = C([outline]).offset(FIT_CLEARANCE, circular_segments=48)
    depth = ARM_THICKNESS + FIT_CLEARANCE
    return pocket.extrude(depth + 1).translate((0,0,-1))

def horn_plate():
    # Existing horn screws into this flat plate via any 3 opposing/symmetric slots.
    # The central service opening passes the original spline-retaining screw.
    plate = disc(24, 5.5) - disc(4.8, 8, -1).rotate((0,0,1.7)) - horn_pocket()
    for a in range(0,360,60):
        slot = (hole(1.25, 8, a, HORN_INNER) + hole(1.25, 8, a, HORN_OUTER)).hull()
        plate -= slot
    for a in (30,150,270):
        plate -= hole(1.7, 8, a, BOLT_CIRCLE)
    return plate

def spacer():
    ring = disc(24, 3.4) - disc(18.5, 5, -1)
    for a in (30,150,270):
        ring -= hole(1.7, 6, a, BOLT_CIRCLE)
    return ring - hole(3.1, 6, 90, ANCHOR_RADIUS)

def drum():
    flange = disc(24,3.2)
    # Add a tapered collar above the flange to avoid a sharp load transition.
    collar = M.cylinder(2.5,17,DRUM_RADIUS,circular_segments=96).translate((0,0,3.1))
    barrel = disc(DRUM_RADIUS,7.2,5.5)
    lip = M.cylinder(3.8,DRUM_RADIUS,18.8,circular_segments=96).translate((0,0,8.9))
    top = disc(18.8,2.6,12.6)
    piece = flange + collar + barrel + lip + top
    piece -= disc(5.0,18,-1)
    # Fastener heads and washers sit on the lower flange outside the cable path.
    for a in (30,150,270):
        piece -= hole(1.7, 6, a, BOLT_CIRCLE)
    # Steel anchor passes through both flanges. The wire eye sits on
    # the smooth shank inside the winding groove.
    piece -= hole(1.35, 18, 90, ANCHOR_RADIUS)
    # Recess the head so the spool can sit under a close-fitting cover.
    piece -= hole(2.35, 1.4, 90, ANCHOR_RADIUS, 14.1)
    return piece

def export(shape, filename):
    m = shape.simplify(0.001).to_mesh()
    part = trimesh.Trimesh(m.vert_properties[:,:3],m.tri_verts)
    assert part.is_volume and len(shape.decompose())==1, filename
    part.export(OUT/filename)
    print(filename, part.extents.round(1), round(part.volume/1000,2))

if __name__ == '__main__':
    export(horn_plate().rotate((180,0,0)).translate((0,0,5.5)),'01-six-arm-fit-plate.stl')
    export(drum(),'02-15mm-cable-drum.stl')
    export(spacer(),'03-fastener-spacer.stl')
