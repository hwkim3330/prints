"""CAD validation of the actuator and example linkage. Hardware fit remains separate."""
from math import cos, sin, radians, hypot, degrees
import cadquery as cq
import model as m

STOP_Z=82
TOWER_X=45
shell=m.lid().rotate((0,0,0),(1,0,0),180).translate((0,0,100))
plate=m.servo_plate().translate((0,0,m.PLATE_Z))
stop=m.stop_sector().translate((0,0,STOP_Z))
riser=m.tower_riser().translate((TOWER_X,15,41))
tower=m.cable_tower().translate((TOWER_X,15,53))
for a,b in ((shell,plate),(shell,stop),(shell,tower),(stop,tower)):
    assert a.intersect(b).val().Volume()<1e-5
for a in range(7,114):
    x=m.SHAFT[0]+20*cos(radians(a))
    y=m.SHAFT[1]+20*sin(radians(a))
    pin=cq.Workplane("XY").center(x,y).circle(1.5).extrude(5).translate((0,0,STOP_Z))
    assert pin.intersect(stop).val().Volume()<1e-5,a

# Example only, in the pedal pivot plane. Measure both geometry and force
# at the actual cable attachment before calculating hardware limits.
anchor_radius=75
rotation=20
guide=(85,-48)
def cable_length(percent):
    angle=radians(-rotation*percent/100)
    return hypot(guide[0]-anchor_radius*cos(angle),guide[1]-anchor_radius*sin(angle))

travel=[cable_length(0)-cable_length(p) for p in range(101)]
assert all(b>a for a,b in zip(travel,travel[1:])), "Cable loses leverage"
print("CAD pin sweep: 7–113 degrees, 107 poses")
print(f"Drum travel for 106 degrees: {m.DRUM_RADIUS*radians(106):.2f} mm")
print(f"Example cable travel: {travel[-1]:.2f} mm, drum sweep: {degrees(travel[-1]/m.DRUM_RADIUS):.1f} deg")
print(f"Example 20 N cable pull and 75% efficiency: {20*m.DRUM_RADIUS/1000/.75:.2f} N m")
