"""A1 carrier for the two SimPedals assemblies. Dimensions in mm."""
from pathlib import Path
import cadquery as cq
OUT=Path(__file__).resolve().parent
# Measured from assembly STEP a5598be66d77a0f93598e20f3e6c94437ad59957.
THROTTLE=(-81,-22)
BRAKE=(22,81)
FORE_AFT=(-75,75)
def slab(w,d,h,r):
    return cq.Workplane("XY").box(w,d,h,centered=(True,True,False)).edges("|Z").fillet(r)
def cut(part,x,y,d):
    return part.cut(cq.Workplane("XY").center(x,y).circle(d/2).extrude(12))
def deck():
    p=slab(246,218,8,10)
    for x in THROTTLE+BRAKE:
        for y in FORE_AFT:
            p=cut(p,x,y,3.6)
    for x in (-110,0,110):
        for y in (-94,94):
            p=cut(p,x,y,6.6)
    # Spare slots for a removable actuator or fairlead bracket.
    for x in (-105,105):
        for y in (-48,0,48):
            slot=cq.Workplane("XY").center(x,y).slot2D(22,4.5,90).extrude(8)
            p=p.cut(slot)
    return p
def coupon():
    p=slab(77,20,4,4)
    for x in (-29.5,29.5):
        p=cut(p,x,0,3.6)
    return p
if __name__=="__main__":
    for n,p in (("A1-SimPedals-Deck",deck()),("59mm-foot-mount-coupon",coupon())):
        assert p.val().isValid() and len(p.solids().vals())==1
        cq.exporters.export(p,str(OUT/f"{n}.stl"),tolerance=.07,angularTolerance=.12)
