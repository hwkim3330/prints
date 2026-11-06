from pathlib import Path
import json,math
import model as m
O=Path(__file__).resolve().parent
# Only rigid CAD checks; no strength or fit certification.
def overlap(a,b):
 q=a.intersect(b)
 return sum(s.Volume() for s in q.solids().vals())
fixed=m.base(); cs=[m.cheek().translate((x,0,8)) for x in (-48,48)]; ca=m.carrier()
ped=m.pedal(78); arm=m.arm()
rows=[]; collisions=[]
for step in range(21):
 a=m.REST-(m.REST-m.DOWN)*step/20;b=m.beta(a)
 p=m.pivot(ped,a); ar=m.arm_pose(arm,b)
 for n,s in [('carrier',ca),('left cheek',cs[0]),('right cheek',cs[1]),('arm',ar)]:
  v=overlap(p,s)
  if v>.05: collisions.append([step,'pedal / '+n,round(v,3)])
 # Move the left pedal onto shared base for all-state check.
 v=overlap(p.translate((-58,0,0)),fixed)
 if v>.05:collisions.append([step,'pedal / base',round(v,3)])
 pin=m.xbore(3,30,-18,m.SY,m.SZ+18)
 v=overlap(ar,pin)
 if v>.05:collisions.append([step,'arm / limit pin',round(v,3)])
 v=overlap(ar,ca)
 if v>.05:collisions.append([step,'arm / carrier',round(v,3)])
 aa=math.radians(a);bb=math.radians(b)
 y=m.SY-m.L*math.cos(bb);z=m.SZ+m.L*math.sin(bb)
 track=y*math.cos(aa)+(z-m.ZP)*math.sin(aa)
 gap=-y*math.sin(aa)+(z-m.ZP)*math.cos(aa)-10-m.RR
 # two extension springs, hypothetical selection to be confirmed physically.
 sy=70*math.cos(aa)-6*math.sin(aa);sz=m.ZP+70*math.sin(aa)+6*math.cos(aa)
 length=math.hypot(sy+10,sz-62)
 spring_force=.6*max(0,length-70)
 moment=2*spring_force*(sy*(62-sz)-(sz-m.ZP)*(-10-sy))/length/1000
 # Gravity mass placeholder 0.15 kg, CoM 65 mm: opposes return.
 gravity=.15*9.80665*.065*math.cos(aa)
 # Positive spring moment alone is an upper estimate of motor demand, neglect friction.
 lever_p=track/1000
 normal_force=moment/lever_p
 motor_torque=normal_force*m.L/1000*abs(math.cos(bb+aa))
 rows.append(dict(percent=step*5,pedal_deg=round(a,3),servo_relative_deg=round(b,3),roller_track_mm=round(track,3),contact_error_mm=round(gap,6),spring_eye_length_mm=round(length,3),spring_only_torque_Nm=round(moment,4),gravity_Nm=round(gravity,4),estimated_servo_Nm=round(motor_torque,4)))
# Manual pressing beyond roller command produces a positive normal separation.
manual=[]
for i in range(21):
 command=m.REST-(m.REST-m.DOWN)*i/20
 bb=math.radians(m.beta(command)); y=m.SY-m.L*math.cos(bb);z=m.SZ+m.L*math.sin(bb)
 for j in range(i,21):
  a=math.radians(m.REST-(m.REST-m.DOWN)*j/20)
  gap=-y*math.sin(a)+(z-m.ZP)*math.cos(a)-18
  manual.append(gap)
# Both axles share the same axis. Include end washer and specified screw head envelope.
pitch = m.CENTERS[1] - m.CENTERS[0]
retainer_stack = m.AXLE_END_WASHER + m.AXLE_HEAD_HEIGHT
axle_tip_gap = pitch - m.AXLE_LENGTH
retainer_gap = axle_tip_gap - 2 * retainer_stack
assert retainer_gap >= 0.5
# Bearing outer face x=32 and cheek inner face x=48-6. The spacer
# bears on the inner race through the cap's central clearance hole.
spacer_width = m.shaft_spacer().val().BoundingBox().zlen
spacer_endplay = 2 * (48 - 6 - 32 - spacer_width)
assert 0 < spacer_endplay <= 1.0
def stop_height(angle, y):
 angle = math.radians(angle)
 return m.ZP + y*math.tan(angle) - 10/math.cos(angle)
# Solid height of the optional manual brake stop at the rear edge of the existing tower.
manual_brake_bumper_mm = stop_height(m.BRAKE_MANUAL_STOP,116) - stop_height(m.DOWN,116)
report={'manual_brake_stop_deg':m.BRAKE_MANUAL_STOP,'manual_brake_stop_added_height_mm':manual_brake_bumper_mm,'adjacent_axle_tip_gap_mm' :axle_tip_gap,'adjacent_retainer_clearance_mm':retainer_gap,'nominal_pedal_endplay_mm':spacer_endplay,'status':'CAD checks only; physical fit/load untested','rigid_collisions_mm3':collisions,'manual_min_gap_mm':min(manual),'angle_states':rows,'toe_travel_mm':148*(math.sin(math.radians(18))-math.sin(math.radians(4))),'servo_sweep_deg':m.beta(18)-m.beta(4),'assumed_spring':{'count_per_pedal':2,'eye_length_unloaded_mm':70,'rate_N_per_mm':.6,'initial_tension_N':0},'warnings':['Spring selection is a calculation example, not a purchased part specification.','MG996R continuous torque unverified.','Horn fit, servo flange and lead outlet require coupon/physical checks.','No FEA or rated human foot load.','Sensors are not included; no sensed pedal input until independent sensors are fitted.']}
(O/'verification.json').write_text(json.dumps(report,indent=2))
print(json.dumps({k:v for k,v in report.items() if k!='angle_states'},indent=2))
assert not collisions
assert min(manual)>-.001
