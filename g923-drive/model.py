"""CadQuery source, mm. Run with cadquery, trimesh and matplotlib installed."""
from pathlib import Path
import cadquery as cq
from math import radians

OUT=Path(__file__).resolve().parent
SERVO_WINDOW=(41.5,20.5)
SERVO_PITCH=(49.5,10)  # fit coupon before committing the mount
DECK=(132,92)
POSTS=[(x,y) for x in (-48,48) for y in (-34,34)]
SHAFT=(-10.35,0)
PLATE_Z=36
PEDAL_STRAP_WIDTH=20
DRUM_RADIUS=15

def slab(w,d,t,r=4):
    return cq.Workplane("XY").box(w,d,t,centered=(True,True,False)).edges("|Z").fillet(r)

def holes(part,points,d):
    return part.faces(">Z").workplane().pushPoints(points).hole(d)

def deck():
    p=holes(slab(*DECK,6,9),POSTS,3.4)
    for x in (-30,30):
        for y in (-34,34):
            p=p.cut(cq.Workplane("XY").center(x,y).slot2D(24,5.5).extrude(6))
    return p

def servo_plate():
    p=slab(108,80,5,6).cut(cq.Workplane("XY").rect(*SERVO_WINDOW).extrude(5))
    for y in (8,22):
        p=p.cut(cq.Workplane("XY").center(38,y).slot2D(19,4.5).extrude(5))
    return holes(holes(p,POSTS,3.4),[(x,y) for x in (-SERVO_PITCH[0]/2,SERVO_PITCH[0]/2)
                                    for y in (-SERVO_PITCH[1]/2,SERVO_PITCH[1]/2)],3.4)

def spacer():
    return cq.Workplane("XY").circle(5).circle(1.7).extrude(PLATE_Z-6)

def cable_tower():
    # Stand is printed on its back. It supports a metal M6 barrel adjuster.
    upright=slab(24,29,6,3)
    upright=holes(upright,[(0,0)],6.5)
    upright=upright.rotate((0,0,0),(0,1,0),90).translate((9,0,14.5))
    foot=holes(slab(34,26,6,3),[(0,-7),(0,7)],4.5)
    # M4 deck slots locate the tower along the cable tangent.
    return foot.union(upright)

def tower_riser():
    return holes(slab(34,26,12,3),[(0,-7),(0,7)],4.5)

def lid():
    # Prints roof-down. Rear notch is open at the rim for attached cables.
    p=slab(130,90,94,9).cut(slab(124,84,92,7).translate((0,0,3)))
    p=p.cut(cq.Workplane("XY").pushPoints(POSTS).circle(1.7).extrude(3))
    for x,y,h in [(65,15,72),(-65,0,24)]:
        p=p.cut(cq.Workplane("XY").box(12,15,h+1).translate((x,y,94-h/2)))
    return p

def saddle():
    # Webbing passes through two slots and wraps the pedal stem. Steel
    # clevis pins through the two ears retain the cable eye.
    p=slab(48,32,5,5)
    for x in (-16,16):
        p=p.cut(cq.Workplane("XY").center(x,0).rect(3.3,PEDAL_STRAP_WIDTH+1).extrude(5))
    for x in (-6,6):
        ear=cq.Workplane("XY").box(5,12,11,centered=(True,True,False)).translate((x,0,4))
        p=p.union(ear)
    return p.cut(cq.Workplane("YZ").center(0,10).circle(2.1).extrude(26,both=True))

def stop_sector():
    # Adjustable guide for a steel stop pin at R20 on the existing drum.
    # Steel washers at the slot ends distribute contact into this plate.
    import math
    angle=math.radians(120)
    a=20
    inner=17.8
    outer=22.2
    slot=(cq.Workplane("XY").moveTo(inner,0)
          .radiusArc((inner*math.cos(angle),inner*math.sin(angle)),-inner)
          .lineTo(outer*math.cos(angle),outer*math.sin(angle))
          .radiusArc((outer,0),outer).close().extrude(5))
    p=holes(slab(108,80,5,6),POSTS,3.4)
    return p.cut(slot.translate((*SHAFT,0))).cut(cq.Workplane("XY").center(*SHAFT).circle(5).extrude(5))

def fit_coupon():
    return servo_plate().intersect(slab(60,30,5,3))

def tower_print():
    rotated=cable_tower().rotate((0,0,0),(0,1,0),90)
    return rotated.translate((0,0,-rotated.val().BoundingBox().zmin))

PARTS={"01-deck":deck,"02-servo-plate":servo_plate,"03-post-x4":spacer,
       "04-cable-tower":tower_print,"05-tower-riser":tower_riser,
       "06-cover":lid,"07-pedal-saddle":saddle,"08-stop-sector":stop_sector,"09-servo-fit-coupon":fit_coupon}
if __name__=="__main__":
    for name,make in PARTS.items():
        part=make()
        assert len(part.solids().vals())==1 and part.val().isValid(),name
        b=part.val().BoundingBox()
        assert max(b.xlen,b.ylen,b.zlen)<256,name
        cq.exporters.export(part,str(OUT/f"{name}.stl"),tolerance=.08,angularTolerance=.12)
        print(name,round(b.xlen,1),round(b.ylen,1),round(b.zlen,1))
