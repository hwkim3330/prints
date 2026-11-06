"""A1-size shared pedal deck with two serviceable under-deck servo pods."""
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec
import cadquery as cq

HERE = Path(__file__).resolve().parent
spec = spec_from_file_location("v2", HERE.parent / "standalone-pedals-v2/model.py")
v2 = module_from_spec(spec)
spec.loader.exec_module(v2)
pedal = v2.pedal
WIDTH = 246
DEPTH = 202
HEIGHT = 104
CHANNEL_X = 61
MOTOR_Y = 58
COLUMNS = [(x,y) for x in (-113,0,113) for y in (-21,140)]

def blank():
    return pedal.slab(WIDTH,DEPTH,7,11).translate((0,59,0))

def column_holes(part):
    for x,y in COLUMNS:
        part = part.cut(pedal.hole(x,y,-1,6.6,9))
    return part

def upper():
    p = blank()
    # Keep the established hinge, stop, cable and sensor hole patterns.
    for center in (-CHANNEL_X,CHANNEL_X):
        for x in (-42,42):
            for y in (-11,11):
                p = p.cut(pedal.hole(center+x,y,-1,5.5,9))
        for x in (-27,27):
            p = p.cut(pedal.hole(center+x,94,-1,8.6,9))
        p = p.cut(pedal.hole(center,65,-1,12,9))
        for x,y in ((-30,78),(30,78),(-15,124),(15,124),(37,45)):
            p = p.cut(pedal.hole(center+x,y,-1,4.5,9))
    return column_holes(p)

def pod_pose(part, brake):
    if brake:
        return part.rotate((0,0,0),(0,0,1),-90).translate((-CHANNEL_X,MOTOR_Y,7))
    return part.rotate((0,0,0),(0,0,1),90).translate((CHANNEL_X,MOTOR_Y,7))

def lower():
    p = column_holes(blank())
    # V2 mounting slots lie at local x +/-30, y +/-34.
    for brake in (False,True):
        for x in (-30,30):
            for y in (-34,34):
                drill = pedal.hole(x,y,-8,5.5,10)
                p = p.cut(pod_pose(drill,brake))
    return p

def side():
    # Cosmetic rail, flat printed. Fasten to angle tabs on the steel columns.
    p = pedal.slab(184,48,2.4,8)
    for x in (-81,81):
        for y in (-15,15):
            p = p.cut(pedal.hole(x,y,-1,4.5,5))
    return p

def assembly():
    result=[("lower",lower()),("upper",upper().translate((0,0,HEIGHT+7)))]
    for x,y in COLUMNS:
        result.append(("column",pedal.hole(x,y,7,12,HEIGHT)))
    for brake in (True,False):
        for name,part in v2.assembly(brake,False):
            oldx = (-1 if brake else 1)*v2.PITCH/2
            part = part.translate((-oldx,0,0))
            if name in ("base","splice"):
                continue
            if name in ("pod deck","servo plate","servo","drum","guide","riser","stop","post"):
                part = pod_pose(part.translate((0,-v2.POD_Y,0)),brake)
            else:
                part = part.translate(((-1 if brake else 1)*CHANNEL_X,0,HEIGHT+7))
            result.append((name,part))
    return result

def verify():
    things=assembly()
    top=things[1][1]
    columns=[shape for name,shape in things if name=="column"]
    podparts=[shape for name,shape in things if name in ("pod deck","servo plate","servo","drum","guide","riser","stop","post")]
    for part in podparts:
        assert part.intersect(top).val().Volume()<.01
        for column in columns:
            assert part.intersect(column).val().Volume()<.01
    half=len(podparts)//2
    for left in podparts[:half]:
        for right in podparts[half:]:
            assert left.intersect(right).val().Volume()<.01
    print("Both pod envelopes, upper deck and six spacer columns clear in CAD.")

if __name__ == "__main__":
    for name,part in (("A1-upper-deck",upper()),("A1-lower-deck",lower()),("Side-trim-x2",side())):
        assert len(part.solids().vals())==1 and part.val().isValid(), name
        b=part.val().BoundingBox()
        assert b.xlen<=246.01 and b.ylen<=246.01
        cq.exporters.export(part,str(HERE/f"{name}.stl"),tolerance=.07,angularTolerance=.12)
    verify()
