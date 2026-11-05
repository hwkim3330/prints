"""Independent pedal cassette. Dimensions in millimetres. Requires CadQuery."""
from pathlib import Path
import cadquery as cq

OUT=Path(__file__).resolve().parent
PIVOT=36
TRAVEL=12
# Assembly coordinates: hinge at y=0, positive y towards toe.
def slab(w,d,h,r=4):
    return cq.Workplane("XY").box(w,d,h,centered=(True,True,False)).edges("|Z").fillet(r)

def hole(x,y,z,d,h):
    return cq.Workplane("XY").center(x,y).circle(d/2).extrude(h).translate((0,0,z))

def crosshole(x,y,z,d,length):
    return cq.Workplane("YZ").center(y,z).circle(d/2).extrude(length).translate((x,0,0))

def base():
    p=slab(120,186,7,9).translate((0,62,0))
    for x in (-49,49):
        for y in (-18,136):
            p=p.cut(hole(x,y,-1,6.6,9))
    for x in (-42,42):
        for y in (-11,11):
            p=p.cut(hole(x,y,-1,5.5,9))
    # Through-bolted rubber stops and a protected cable exit through the rig.
    for x in (-27,27):
        p=p.cut(hole(x,94,-1,8.6,9))
    p=p.cut(hole(0,65,-1,12,9))
    for x,y in ((-30,78),(30,78),(-15,124),(15,124),(37,45)):
        p=p.cut(hole(x,y,-1,4.5,9))
    return p

def hinge():
    # Print laid on the flat outer cheek. An M8 smooth shaft spans both cheeks.
    p=slab(18,34,7,3)
    for y in (-11,11):
        p=p.cut(hole(0,y,-1,5.5,9))
    p=p.union(slab(12,26,37,4).translate((0,0,6)))
    p=p.cut(crosshole(-8,0,PIVOT-7,8.3,16))
    return p

def pedal(width):
    # Bottom face at z=39. Top face takes a bolted metal tread.
    p=slab(width,141,9,8).translate((0,57.5,39))
    for x in (-25,25):
        p=p.union(slab(12,22,13,3).translate((x,0,31)))
    for x in (-43,43):
        p=p.cut(cq.Workplane("XY").center(x,0).box(18,38,24).translate((0,0,40)))
    p=p.cut(crosshole(-36,0,PIVOT,8.3,72))
    for x in (-23,23):
        for y in (28,112):
            p=p.cut(hole(x,y,38,5.5,11))
    for x,y in ((0,65),(-30,78),(30,78),(-15,124),(15,124),(37,45)):
        p=p.cut(hole(x,y,38,4.5,11))
    return p

def sensor_post():
    # Uncommitted carrier for an analog linear Hall breakout, secured by a tie.
    p=slab(21,27,16,3)
    p=p.cut(hole(0,0,-1,4.5,26))
    for y in (-8,8):
        p=p.cut(cq.Workplane("XY").center(0,y).rect(16,3).extrude(7).translate((0,0,10)))
    return p

def fixture_coupon():
    p=slab(50,33,6,3)
    for x,d in ((-15,8.2),(0,8.3),(15,8.5)):
        p=p.cut(hole(x,0,-1,d,8))
    return p

def lay(p,axis=None):
    if axis: p=p.rotate((0,0,0),axis,90 if axis[1] else 180)
    return p.translate((0,0,-p.val().BoundingBox().zmin))

PARTS={
    "01-base-x2":base,
    "02-hinge-x4":lambda:lay(hinge(),(0,1,0)),
    "03-accel":lambda:lay(pedal(84),(1,0,0)),
    "04-brake":lambda:lay(pedal(96),(1,0,0)),
    "05-hall-post-x2":sensor_post,
    "06-axle-fit-coupon":fixture_coupon,
}
if __name__=="__main__":
    for name,fn in PARTS.items():
        part=fn()
        assert len(part.solids().vals())==1 and part.val().isValid(),name
        bbox=part.val().BoundingBox()
        assert max(bbox.xlen,bbox.ylen,bbox.zlen)<256
        cq.exporters.export(part,str(OUT/f"{name}.stl"),tolerance=.06,angularTolerance=.1)
        print(name,round(bbox.xlen,1),round(bbox.ylen,1),round(bbox.zlen,1))
