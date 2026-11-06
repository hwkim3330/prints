"""PETG-only twin pedal motion mockup. No foot-load rating."""
from pathlib import Path
from math import cos, radians, tan
import cadquery as cq

OUT = Path(__file__).resolve().parent
PIVOT_Z = 33
SHAFT_D = 16
SHAFT_LENGTH = 232
CENTERS = (-53, 53)

def block(width, length, height, x=0, y=0, z=0):
    return cq.Workplane("XY").box(width, length, height, centered=(True,True,False)).translate((x,y,z))

def rounded(width, length, height, radius, y=0):
    return block(width,length,height).edges("|Z").fillet(radius).translate((0,y,0))

def cross_bore(diameter, length, x, y=0, z=PIVOT_Z):
    return cq.Workplane("YZ").circle(diameter/2).extrude(length).translate((x,y,z))

def base():
    shape = rounded(244,212,8,12,82)
    for x in (-106,0,106):
        # Wide, sloping supports transfer hinge load into the full base.
        tower = (cq.Workplane("YZ").polyline([(-23,7),(28,7),(15,33),(11,45),
                   (-11,45),(-17,29)]).close().extrude(7,both=True).translate((x,0,0)))
        shape = shape.union(tower)
        shape = shape.cut(cross_bore(16.6,18,x-9))
    for x in CENTERS:
        heel_angle = radians(14)
        heel_height = PIVOT_Z - 24*tan(heel_angle) + 5/cos(heel_angle)
        shape = shape.union(rounded(54,6,heel_height-7,2,-21).translate((x,0,7)))
        shape = shape.union(rounded(72,10,24,4,109).translate((x,0,7)))
    return shape

def pedal(width):
    face = rounded(width,150,8,8,49).translate((0,0,5))
    hub = cross_bore(34,width-4,-(width-4)/2,0,0)
    shape = face.union(hub)
    for x in (-width/2+8,width/2-8):
        shape = shape.union(block(10,130,12,x,50,-6))
    return shape.cut(cross_bore(16.7,width+2,-width/2-1,0,0))

def shaft():
    # Print flat along the axis. Facet provides a continuous bed contact.
    rod = cross_bore(SHAFT_D,SHAFT_LENGTH,-SHAFT_LENGTH/2,0,0)
    rod = rod.cut(block(240,24,4,0,0,-10))
    for x in (-115,113):
        full = cross_bore(17,2,x,0,0)
        core = cross_bore(12,2,x,0,0)
        rod = rod.cut(full.cut(core))
    return rod

def clip():
    ring = cq.Workplane("XY").circle(10.5).circle(6.15).extrude(1.65)
    return ring.cut(block(9.5,13,3,0,6.5,-.5))

def spacer(length):
    return cq.Workplane("XY").circle(11).circle(8.35).extrude(length)

def fit_coupon():
    shoe = rounded(42,24,5,3)
    pad = shoe.union(block(16,24,17,0,0,4))
    return pad.cut(cross_bore(16.7,20,-10,0,12))

def pose(shape, angle, x):
    return shape.rotate((0,0,0),(1,0,0),angle).translate((x,0,PIVOT_Z))

def ground(shape):
    return shape.translate((0,0,-shape.val().BoundingBox().zmin))

def export():
    parts = {"01-base":base(),"02-throttle":ground(pedal(76).rotate((0,0,0),(1,0,0),180)),
             "03-brake":ground(pedal(88).rotate((0,0,0),(1,0,0),180)),
             "04-shaft":ground(shaft()),"05-clip-x2":clip(),"06-throttle-spacer-x2":spacer(7.75),
             "07-brake-spacer-x2":spacer(1.75),"00-bore-coupon":fit_coupon(),
             "00-shaft-coupon":ground(shaft().intersect(block(24,24,24,-104,0,-12)))}
    for name,shape in parts.items():
        assert shape.val().isValid() and len(shape.solids().vals()) == 1, name
        assert max(shape.val().BoundingBox().xlen,shape.val().BoundingBox().ylen) <= 244.01
        cq.exporters.export(shape,str(OUT/f"{name}.stl"),tolerance=.07,angularTolerance=.13)
    assembly = cq.Assembly()
    assembly.add(base(),name="base")
    assembly.add(shaft().translate((0,0,PIVOT_Z)),name="shaft")
    for index,(center,width) in enumerate(zip(CENTERS,(88,76))):
        assembly.add(pose(pedal(width),12,center),name=f"pedal-{index}")
    assembly.save(str(OUT/"assembly.step"))
    # Ensure the rotating footboards clear one another and hinge towers.
    # Intentional base contact below the travel range is excluded.
    fixed = base()
    for angle in range(7,14):
        for center,width in zip(CENTERS,(88,76)):
            collision = fixed.intersect(pose(pedal(width),angle,center))
            assert sum(s.Volume() for s in collision.solids().vals()) < .1, (angle,center)

if __name__ == "__main__":
    export()
