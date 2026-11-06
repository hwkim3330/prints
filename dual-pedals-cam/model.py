"""Printed two-channel servo pedal test geometry, millimetres."""
from pathlib import Path
import json, math
import cadquery as cq
import passive as p

OUT = Path(__file__).resolve().parent
SY, SZ, ARM = 146, 65, 43
REST = 13
ENDS = (9, 7)
PAD_R = 5
MOUNT_X = -7

def spring(thickness):
    # Lay the whole leaf on the bed, with its length in the XY plane.
    leaf = p.block(12,72,thickness,-2,114,0)
    root = p.block(22,16,8,0,154,0)
    tip = p.block(12,8,10,-2,81,0).edges('|X').fillet(1.7)
    return leaf.union(root).union(tip)

def base():
    shape = p.base()
    for x in p.CENTERS:
        # Cantilever is inserted along Y. Its root slides between roof and shelf.
        for side in (-1,1):
            shape = shape.union(p.block(5,22,47,x+20+side*13.8,155,8))
            shape = shape.union(p.block(8,22,4,x+20+side*13,155,54))
        shape = shape.union(p.block(29,22,5,x+20,155,45))
        shape = shape.union(p.block(29,4,10,x+20,168,48))
        # Vertical socket for servo carrier tongue.
        for y in (135,177):
            shape = shape.union(p.block(30,6,17,x-27+MOUNT_X,y,8))
        for side in (-1,1):
            shape = shape.union(p.block(5,48,17,x-27+MOUNT_X+side*13,156,8))
    return shape

def cradle():
    # Servo slides through the window. Stock flange is caught between
    # carrier and removable printed slide cap.
    plate = p.block(7,58,39,-12,156,48)
    plate = plate.cut(p.block(10,41.6,21.2,-12,156,54.4))
    tongue = p.block(20.5,35.1,17,-27,156,9)
    upright = (cq.Workplane('XZ').polyline([(-39,23),(-14,23),(-8.5,54),
                  (-15.5,54),(-39,34)]).close().extrude(5).translate((0,185,0)))
    # Wide back wall links tongue to the flange plate beyond servo leads.
    wall = p.block(7,9,34,-12,184.6,22)
    return tongue.union(p.block(20,18,5,-27,176,25.2)).union(upright).union(wall).union(plate).translate((MOUNT_X,0,0))

def keeper():
    # Open U slides down over flange edges; test flange before using.
    bridge = p.block(10,58,5,-20.55,156,78)
    for y in (130,182):
        bridge = bridge.union(p.block(10,5,25.8,-20.55,y,54.2))
        bridge = bridge.union(p.block(4,8,6,-23,y,54))
    return bridge.translate((MOUNT_X,0,0))

def horn(clearance=.3):
    # Six stock arms; these nominal values still require the existing fit gauge.
    pts=[]
    tip=2.3
    sector=[(8.1*math.cos(math.pi/6),-4.05),(8.8,-3.66)]
    sector += [(13.7+tip*math.cos(math.radians(a)),tip*math.sin(math.radians(a)))
               for a in range(-90,91,10)]
    sector += [(8.8,3.66)]
    for i in range(6):
        a=i*math.pi/3
        pts += [(x*math.cos(a)-y*math.sin(a),x*math.sin(a)+y*math.cos(a)) for x,y in sector]
    return cq.Workplane('XY').polyline(pts).close().offset2D(clearance).extrude(2.4)

def cam():
    disc=cq.Workplane('XY').circle(21).extrude(8)
    lever=cq.Workplane("XY").polyline([(8,-7),(21,-20),(34,-15),(46,-3),(44,4),(31,-8),(21,-12),(11,0)]).close().extrude(8)
    nose=cq.Workplane('XY').center(ARM,0).circle(PAD_R).extrude(8)
    # Axial captivity needs the stock screw and verified hub stack.
    return disc.union(lever).union(nose).cut(horn()).cut(cq.Workplane('XY').circle(1.7).extrude(9)).cut(cq.Workplane('XY',origin=(0,0,3.2)).circle(4).extrude(6))

def beta(angle):
    a=math.radians(angle)
    return math.asin((13+PAD_R+SY*math.sin(a)-(SZ-p.PIVOT_Z)*math.cos(a))/ARM)-a

def cam_pose(angle,x):
    b=math.degrees(beta(angle))
    return cam().rotate((0,0,0),(0,1,0),90).rotate((0,0,0),(1,0,0),-90-b).translate((x-5.4,SY,SZ))

def socket_coupon():
    # Cut directly from the throttle side of the production base.
    return p.ground(base().intersect(p.block(91,58,59,48,159,6)))

def horn_coupon():
    plate = p.rounded(116,39,4,4)
    for x, clearance in ((-38,.2),(0,.3),(38,.4)):
        plate = plate.cut(horn(clearance).translate((x,0,1.6)))
    return plate

def export():
    shapes={'00-socket-gauge':socket_coupon(),'00-horn-gauge':horn_coupon(),'01-base':base(),'02-brake':p.pedal(88),'03-throttle':p.pedal(76),
            '04-shaft':p.shaft(),'05-clip-x2':p.clip(),'06-throttle-spacer-x2':p.spacer(7.75),
            '07-brake-spacer-x2':p.spacer(1.75),'08-brake-leaf':spring(3.2),
            '09-throttle-leaf':spring(2.4),'10-cradle-x2':cradle(),'11-keeper-x2':keeper(),
            '12-cam-x2':cam()}
    for name,shape in shapes.items():
        if name in ('02-brake','03-throttle','12-cam-x2'):
            shape=shape.rotate((0,0,0),(1,0,0),180)
        if name in ('10-cradle-x2','11-keeper-x2'):
            shape=shape.rotate((0,0,0),(0,1,0),90)
        shape=p.ground(shape)
        assert shape.val().isValid() and len(shape.solids().vals())==1,name
        cq.exporters.export(shape,str(OUT/(name+'.stl')),tolerance=.07,angularTolerance=.13)
    scene=cq.Assembly()
    scene.add(base(),name='base')
    scene.add(p.shaft().translate((0,0,p.PIVOT_Z)),name='axle')
    report=[]
    fixed = base()
    def overlap(first, second):
        return sum(solid.Volume() for solid in first.intersect(second).solids().vals())
    for x,width,end in zip(p.CENTERS,(88,76),ENDS):
        scene.add(p.pose(p.pedal(width),REST,x),name=f'pedal-{x}')
        scene.add(cam_pose(REST,x),name=f'cam-{x}')
        scene.add(cradle().translate((x,0,0)),name=f'cradle-{x}')
        scene.add(keeper().translate((x,0,0)),name=f'keeper-{x}')
        # The simple spring model is the unloaded print geometry.
        scene.add(spring(3.2 if width==88 else 2.4).translate((x+20,0,50)),name=f'leaf-{x}')
        mount = cradle().translate((x,0,0))
        assert overlap(mount,fixed)<.05
        assert overlap(mount,keeper().translate((x,0,0)))<.05
        separations=[]
        max_overlap=0
        for i in range(11):
            a=REST-(REST-end)*i/10
            arm=cam_pose(a,x)
            pedal=p.pose(p.pedal(width),a,x)
            max_overlap=max(max_overlap,overlap(arm,fixed),overlap(arm,mount),
                            overlap(arm,pedal),overlap(pedal,fixed))
            b=beta(a)
            y=SY-ARM*math.cos(b)
            z=SZ+ARM*math.sin(b)
            for j in range(i,11):
                t=math.radians(REST-(REST-end)*j/10)
                separations.append(-y*math.sin(t)+(z-p.PIVOT_Z)*math.cos(t)-13-PAD_R)
        assert min(separations)>-1e-6
        assert max_overlap<.05,(x,max_overlap)
        report.append({'width_mm':width,'pedal_degrees':[REST,end],
                       'max_rigid_intersection_mm3':max_overlap,'servo_sweep_deg':math.degrees(beta(REST)-beta(end)),
                       'minimum_analytical_pad_separation_mm':min(separations)})
    scene.save(str(OUT/'assembly.step'))
    (OUT/'kinematics.json').write_text(json.dumps(report,indent=2))

if __name__=='__main__':
    export()
