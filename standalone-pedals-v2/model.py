"""Two independent pedal cassettes with integrated MG996R pods. CAD in mm."""
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec
import cadquery as cq

HERE = Path(__file__).resolve().parent

def load(name, sibling):
    spec = spec_from_file_location(name, HERE.parent / sibling / "model.py")
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

pedal = load("pedal", "standalone-pedals")
drive = load("drive", "g923-drive")
POD_Y = -78
PITCH = 138
BRIDGE_Y = -36
TOWER_X = 45

def pod_deck():
    p = drive.deck()
    for x in (-49,49):
        p = p.cut(pedal.hole(x,24,-1,6.6,8))
    return p

def splice():
    # PETG locating bar; M6 fasteners continue through to the rigid rig plate.
    p = pedal.slab(20,58,6,5)
    for y in (-18,18):
        p = p.cut(pedal.hole(0,y,-1,6.6,8))
    return p

def cover():
    # Roof-down print. Thin cosmetic walls; the four screws carry the cover.
    outer = drive.slab(130, 90, 94, 9).faces("<Z").edges().chamfer(.6)
    cavity = drive.slab(126, 86, 93, 7.5).translate((0, 0, 2.4))
    cover = outer.cut(cavity)
    cover = cover.cut(cq.Workplane("XY").pushPoints(drive.POSTS).circle(1.7).extrude(3))
    for x, y, height in ((65, 15, 72), (-65, 0, 24)):
        cut = cq.Workplane("XY").box(12, 15, height + 1)
        cover = cover.cut(cut.translate((x, y, 94 - height / 2)))
    return cover

def mirror(part):
    return part.mirror("YZ")

def assembly(brake=False, covered=True):
    hand = -1 if brake else 1
    offset = hand*PITCH/2
    shapes = [
        ("base",pedal.base()),
        ("pedal",pedal.pedal(96 if brake else 84)),
        ("metal tread",pedal.slab(89 if brake else 77,115,2,6).translate((0,63,48))),
        ("Hall post",pedal.sensor_post().translate((37,45,7))),
        ("axle",pedal.crosshole(-54,0,36,8,108)),
    ]
    for x in (-42,42):
        shapes.append(("hinge",pedal.hinge().translate((x,0,7))))
    for x in (-49,49):
        shapes.append(("splice",splice().translate((x,BRIDGE_Y,-6))))
    pod=[
        ("pod deck",pod_deck()),
        ("servo plate",drive.servo_plate().translate((0,0,36))),
        ("servo",pedal.slab(40.7,19.7,36,1.2).translate((0,0,12))),
        ("drum",cq.Workplane("XY").circle(24).extrude(5).faces(">Z").workplane()
         .circle(15).extrude(8).faces(">Z").workplane().circle(19).extrude(3)
         .translate((*drive.SHAFT,58))),
        ("guide",drive.cable_tower().translate((TOWER_X,15,53))),
        ("riser",drive.tower_riser().translate((TOWER_X,15,41))),
        ("stop",drive.stop_sector().translate((0,0,82))),
    ]
    for x,y in drive.POSTS:
        pod.append(("post",drive.spacer().translate((x,y,6))))
    if covered:
        pod.append(("cover",cover().rotate((0,0,0),(1,0,0),180).translate((0,0,100))))
    for name,part in pod:
        if brake: part=mirror(part)
        shapes.append((name,part.translate((0,POD_Y,0))))
    return [(name,part.translate((offset,0,0))) for name,part in shapes]

SHARED={
    "pedal-base":pedal.base,
    "hinge":pedal.PARTS["02-hinge-x4"],
    "accel-tread-carrier":pedal.PARTS["03-accel"],
    "brake-tread-carrier":pedal.PARTS["04-brake"],
    "hall-mount":pedal.sensor_post,
    "splice":splice,
    "pod-post":drive.spacer,
    "guide-riser":drive.tower_riser,
    "axle-fit-coupon":pedal.fixture_coupon,
}
HANDED={
    "motor-base":pod_deck,
    "motor-plate":drive.servo_plate,
    "cable-guide":drive.tower_print,
    "cover":cover,
    "rotation-stop":drive.stop_sector,
}
PARTS={name:fn() for name,fn in SHARED.items()}
for name,fn in HANDED.items():
    part=fn()
    PARTS[f"accel-{name}"]=part
    PARTS[f"brake-{name}"]=mirror(part)

if __name__=="__main__":
    for name,part in PARTS.items():
        assert len(part.solids().vals())==1 and part.val().isValid(),name
        bbox=part.val().BoundingBox()
        assert bbox.xlen<250 and bbox.ylen<250 and bbox.zlen<250,name
        cq.exporters.export(part,str(HERE/f"{name}.stl"),tolerance=.07,angularTolerance=.12)
    # Check the paired envelopes and nominal splice/deck position.
    for brake in (False,True):
        parts=dict(assembly(brake))
        assert parts["base"].intersect(parts["pod deck"]).val().Volume()<0.01
        for name in ("servo plate","stop","guide"):
            assert parts["cover"].intersect(parts[name]).val().Volume()<0.01
    print(f"{len(PARTS)} valid printable solids; both pod envelopes checked")
