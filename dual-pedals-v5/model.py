"""Independent low-force dual pedal bench prototype. mm / degrees.
Original CAD; reference decisions in README. Hardware dimensions are nominal.
Run with CadQuery 2.6+. No firmware or physical motion.
"""
from pathlib import Path
import math,json
import cadquery as cq
O=Path(__file__).resolve().parent
CENTERS=(-58,58); ZP=38; SY=175; SZ=68; L=55; RR=8
REST=18; DOWN=4
HORN_OD=32; HORN_ROOT=7.32; HORN_TIP=4.6; HORN_VALLEY=8.1
HORN_THICK=2; CLEAR=.3; HORN_HOLES=(6.5,14.5)
def box(w,d,h,x=0,y=0,z=0):
 return cq.Workplane('XY').box(w,d,h,centered=(True,True,False)).translate((x,y,z))
def slab(w,d,h,x=0,y=0,z=0,r=2):
 return box(w,d,h).edges('|Z').fillet(r).translate((x,y,z))
def bore(d,h,x=0,y=0,z=0):
 return cq.Workplane('XY').circle(d/2).extrude(h).translate((x,y,z))
def xbore(d,h,x=0,y=0,z=0):
 return cq.Workplane('YZ').circle(d/2).extrude(h).translate((x,y,z))
def pivot(p,a): return p.rotate((0,0,0),(1,0,0),a).translate((0,0,ZP))
def beta(a):
 # Roller centre lies RR above the pedal top plane, measured normally.
 a=math.radians(a)
 q=(10+RR+SY*math.sin(a)-(SZ-ZP)*math.cos(a))/L
 return math.degrees(math.asin(q)-a)
def arm_pose(p,b):
 # Local model: x along arm (toward toe), y sideways, z thickness.
 return p.rotate((0,0,0),(0,1,0),90).rotate((0,0,0),(1,0,0),-90-b).translate((1,SY,SZ))
def base():
 p=slab(242,242,8,y=97,r=10)
 for x in (-117,0,117): p=p.union(slab(5,226,5,x,97,8,r=2))
 for c in CENTERS:
  for x in (-48,48):
   for y in (-12,12): p=p.cut(bore(5.5,10,c+x,y,-1))
  for x in (-36,-6):
   for y in (157,207): p=p.cut(bore(5.5,10,c+x,y,-1))
  # Stops carry load to base, not to servo. Mount base to rigid backing.
  for x in (-24,24):
   up=ZP+math.tan(math.radians(REST))*(-22)-10/math.cos(math.radians(REST))
   dn=ZP+math.tan(math.radians(DOWN))*116-10/math.cos(math.radians(DOWN))
   p=p.union(box(12,8,up-8,c+x,-18,8))
   p=p.union(box(12,8,dn-8,c+x,120,8))
   p=p.cut(bore(5.5,50,c+x,120,-1))
 for x in (-108,108):
  for y in (36,135,207): p=p.cut(bore(6.6,16,x,y,-1))
 return p

def cheek():
 p=slab(20,36,8,r=2)
 profile=[(-18,7),(18,7),(18,35),(-1,64),(-18,64)]
 p=p.union(cq.Workplane('YZ').polyline(profile).close().extrude(6,both=True))
 p=p.cut(xbore(8.3,22,-11,0,30))
 p=p.cut(cq.Workplane('YZ').center(-10,54).slot2D(10,3.5).extrude(22).translate((-11,0,0)))
 for y in (-12,12): p=p.cut(bore(5.5,9,0,y,-.5))
 # bolt heads need access from foot top; remove upright over them.
 for y in (-12,12): p=p.cut(bore(10,12,0,y,8))
 return p

def pedal(width):
 p=slab(width,174,8,y=61,z=2,r=7)
 p=p.union(xbore(32,64,-32,0,0))
 for x in (-24,24):
  p=p.union(box(10,164,12,x,56,-10))
  # side spring ears outside the shoe contact surface.
 for x in (-43,43):
  p=p.union(slab(20,16,8,x,70,2,r=3))
  p=p.cut(bore(3.5,12,x,70,0))
 p=p.cut(xbore(9,70,-35,0,0))
 for z in (-13,13): p=p.cut(xbore(3.4,72,-36,0,z))
 for x in (-32,25): p=p.cut(xbore(22.2,7,x,0,0))
 # shallow grip grooves stop short of roller track at local x=10..26.
 for y in range(30,141,14):
  p=p.cut(box(width-12,2,1,0,y,9))
 # preserve smooth roller track above groove cuts.
 p=p.union(box(20,125,1,18,82.5,9))
 return p

def carrier():
 # upright YZ plate at x=-12; open servo pocket and rear lead clearance.
 p=slab(48,66,7,-25,182,8,r=3)
 plate=box(7,68,79,-13.5,185,15)
 plate=plate.cut(box(12,41.5,21,-13.5,185,57.5))
 for y in (160.25,209.75):
  for z in (63,73): plate=plate.cut(xbore(3.5,12,-20,y,z))
 plate=plate.cut(xbore(3.4,12,-20,SY,SZ+18))
 p=p.union(plate)
 # Triangle gussets alongside servo ends; avoid its nominal case envelope.
 for y in (153,214):
  g=cq.Workplane('XZ').polyline([(-48,15),(-17,15),(-17,80)]).close().extrude(4).translate((0,y,0))
  p=p.union(g)
 for x in (-36,-6):
  for y in (157,207): p=p.cut(bore(5.5,10,x,y,7))
 # cable tie slots in rear flange, clear of servo body.
 for x in (-36,-25): p=p.cut(box(3,9,10,x,211,7))
 return p

def horn_outline(clear=CLEAR):
 # User's paper option 01 reference profile: straight taper, rounded tips.
 pts=[]; tip=HORN_TIP/2; tc=HORN_OD/2-tip
 one=[(HORN_VALLEY*math.cos(math.pi/6),-HORN_VALLEY*.5),(8.8,-HORN_ROOT/2)]
 one += [(tc+tip*math.cos(math.radians(t)),tip*math.sin(math.radians(t))) for t in range(-90,91,10)]
 one += [(8.8,HORN_ROOT/2)]
 for deg in range(0,360,60):
  a=math.radians(deg)
  pts += [(x*math.cos(a)-y*math.sin(a),x*math.sin(a)+y*math.cos(a)) for x,y in one]
 w=cq.Workplane('XY').polyline(pts).close()
 return w.offset2D(clear) if clear else w

def arm():
 p=bore(44,8).union(cq.Workplane('XY').polyline([(8,-16),(28,-38),(49,-23),(60,-5),(60,5),(50,5),(40,-15),(28,-25),(17,-9)]).close().extrude(8)).union(bore(12,8,L,0))
 p=p.cut(horn_outline().extrude(HORN_THICK+CLEAR))
 p=p.cut(bore(9.6,10,z=-1))
 for a in (0,120,240):
  mid=sum(HORN_HOLES)/2; leng=HORN_HOLES[1]-HORN_HOLES[0]+2.5
  s=cq.Workplane('XY').center(mid,0).slot2D(leng,2.5).extrude(10).translate((0,0,-1)).rotate((0,0,0),(0,0,1),a)
  p=p.cut(s)
 # Captive fixed M3 stop pin in a curved slot, 2 deg beyond commanded range.
 for k in range(81):
  angle=math.radians(-90+beta(DOWN)-2+(beta(REST)-beta(DOWN)+4)*k/80)
  p=p.cut(bore(3.6,10,18*math.cos(angle),18*math.sin(angle),-1))
 p=p.cut(bore(5.3,10,L,0,-1))
 return p

def bearing_cap():
 p=bore(32,3).cut(bore(14,5,z=-1))
 for y in (-13,13): p=p.cut(bore(3.4,5,0,y,-1))
 return p

def roller():
 # 625 bearing outer races are the actual rollers. Printed spacer only.
 return bore(7.6,2).cut(bore(5.3,4,z=-1))
def shaft_spacer(): return bore(12,9.5).cut(bore(8.4,12,z=-1))
def coupon():
 p=slab(96,48,5,r=3)
 p=p.cut(horn_outline().extrude(HORN_THICK+CLEAR))
 for x,d in ((-34,8.3),(30,22.2)):
  p=p.cut(bore(d,7,x,0,-1))
 return p

def servo_coupon():
 p=slab(68,36,4,r=3).cut(box(41.5,21,6,0,0,-1))
 for x in (-24.75,24.75):
  for y in (-5,5):p=p.cut(bore(3.5,6,x,y,-1))
 return p

def sensor_mount():
 p=slab(20,30,4,r=2)
 for y in (-10,10): p=p.cut(cq.Workplane('XY').center(0,y).slot2D(12,3.4).extrude(6))
 return p

def grounded(p): return p.translate((0,0,-p.val().BoundingBox().zmin))
def parts():
 return {'01-common-base':base(),'02-cheek-x4':grounded(cheek().rotate((0,0,0),(0,1,0),90)),
 '03-throttle':grounded(pedal(70).rotate((0,0,0),(1,0,0),180)),
 '04-brake':grounded(pedal(78).rotate((0,0,0),(1,0,0),180)),
 '05-servo-carrier-x2':grounded(carrier().rotate((0,0,0),(0,1,0),-90)),
 '06-six-arm-lever-x2':grounded(arm().rotate((0,0,0),(1,0,0),180)),
 '07-roller-spacer-x2':roller(),'08-axle-spacer-x4':shaft_spacer(),'00-fit-coupon':coupon(),'09-bearing-cap-x4':bearing_cap(),'10-servo-fit-coupon':servo_coupon()}

def assembly(a=REST,explode=False):
 out=[('base',base())]; lift=40 if explode else 0
 for i,c in enumerate(CENTERS):
  out.append(('pedal',pivot(pedal(78 if i==0 else 70),a).translate((c,0,lift))))
  for x in (-48,48): out.append(('cheek',cheek().translate((c+x,0,8+lift))))
  out.append(('carrier',carrier().translate((c,0,lift))))
  # Servo nominal envelope only; flange near x=-10, output shaft along X.
  out.append(('servo',box(36,40,20,c-30,185,58+lift)))
  out.append(('arm',arm_pose(arm(),beta(a)).translate((c,0,lift))))
  b=math.radians(beta(a)); yy=SY-L*math.cos(b); zz=SZ+L*math.sin(b)
  for x in (11,16): out.append(('bearing',xbore(16,5,c+x,yy,zz+lift).cut(xbore(5,7,c+x-1,yy,zz+lift))))
  out.append(('axle',xbore(8,120,c-60,0,ZP+lift)))
  for x in (-32,25): out.append(('bearing',pivot(xbore(22,7,x).cut(xbore(8,9,x-1)),a).translate((c,0,lift))))
  for x in (-35,32): out.append(('bearing',pivot(bearing_cap().rotate((0,0,0),(0,1,0),90).rotate((0,0,0),(1,0,0),90).translate((x,0,0)),a).translate((c,0,lift))))
  # Spring axes are shown as lines in diagram, not invented coil geometry.
 return out

if __name__=='__main__':
 meta={}
 for name,p in parts().items():
  assert p.val().isValid() and len(p.solids().vals())==1,name
  bb=p.val().BoundingBox(); assert max(bb.xlen,bb.ylen)<246 and bb.zlen<256,name
  cq.exporters.export(p,str(O/(name+'.stl')),tolerance=.06,angularTolerance=.12)
  meta[name]={'bbox_mm':[round(v,2) for v in (bb.xlen,bb.ylen,bb.zlen)],'volume_cm3':round(p.val().Volume()/1000,2)}
  print(name,meta[name],flush=True)
 ass=cq.Assembly()
 for i,(n,p) in enumerate(assembly()):ass.add(p,name=f'{n}-{i}')
 ass.save(str(O/'assembly.step'))
 (O/'parts.json').write_text(json.dumps(meta,indent=2))
