from pathlib import Path
import cadquery as cq
import model as m
O=Path(__file__).resolve().parent
ps=m.parts()
def place(name,x,y):
 p=ps[name];b=p.val().BoundingBox()
 return p.translate((x-b.xmin,y-b.ymin,-b.zmin))
layouts={
'A-base':[('01-common-base',0,0)],
'B-pedals':[('03-throttle',0,0),('04-brake',118,0)],
'C-hardware':[('02-cheek-x4',x,y) for x in (0,74) for y in (0,46)]+[('06-six-arm-lever-x2',x,96) for x in (0,94)]+[('09-bearing-cap-x4',x,169) for x in (0,40,80,120)]+[('08-axle-spacer-x4',185,y) for y in (0,22,44,66)]+[('07-roller-spacer-x2',185,y) for y in (90,110)],
'E-carriers':[('05-servo-carrier-x2',x,0) for x in (0,100)],
'D-fit-coupon':[('00-fit-coupon',0,0),('10-servo-fit-coupon',0,60)]}
for name,layout in layouts.items():
 p=cq.Compound.makeCompound([place(n,x,y).val() for n,x,y in layout]);b=p.BoundingBox()
 assert max(b.xlen,b.ylen)<=242
 cq.exporters.export(p,str(O/(name+'.stl')),tolerance=.06,angularTolerance=.12)
 print(name,len(layout),b.xlen,b.ylen,flush=True)
