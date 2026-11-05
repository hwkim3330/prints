"""MG996R six-arm horn adapter, dimensions in mm."""
from pathlib import Path
from math import cos, sin, radians
from manifold3d import Manifold as M, CrossSection as C
import trimesh

OUT = Path(__file__).resolve().parent
HORN_INNER = 7.5
HORN_OUTER = 17
DRUM_RADIUS = 15
BOLT_CIRCLE = 20

def disc(r, h, z=0):
    return M.cylinder(h, r, circular_segments=96).translate((0,0,z))

def hole(r, h, angle, radius, z=-1):
    a = radians(angle)
    return disc(r,h,z).translate((radius*cos(a),radius*sin(a),0))

def horn_plate():
    # Existing horn screws into this flat plate via any 3 opposing/symmetric slots.
    # The central service opening passes the original spline-retaining screw.
    plate = disc(24, 4.5) - disc(4.8, 7, -1)
    for a in range(0,360,60):
        slot = (hole(1.25, 7, a, HORN_INNER) + hole(1.25, 7, a, HORN_OUTER)).hull()
        plate -= slot
    for a in (30,150,270):
        plate -= hole(1.7, 7, a, BOLT_CIRCLE)
    return plate

def spacer():
    ring = disc(24, 3.4) - disc(18.5, 5, -1)
    for a in (30,150,270):
        ring -= hole(1.7, 6, a, BOLT_CIRCLE)
    return ring

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
    # Tie the cable through the upper flange into the exposed winding groove.
    piece -= hole(1.1, 4, 90, 16.8, 12)
    return piece

def export(shape, filename):
    m = shape.to_mesh()
    part = trimesh.Trimesh(m.vert_properties[:,:3],m.tri_verts)
    assert part.is_volume and len(shape.decompose())==1, filename
    part.export(OUT/filename)
    print(filename, part.extents.round(1), round(part.volume/1000,2))

if __name__ == '__main__':
    export(horn_plate(),'01-six-arm-fit-plate.stl')
    export(drum(),'02-15mm-cable-drum.stl')
    export(spacer(),'03-fastener-spacer.stl')
