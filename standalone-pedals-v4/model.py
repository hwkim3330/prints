"""Low-profile shared A1 base and vertical MG996R carriers."""
from pathlib import Path
import cadquery as cq
from importlib.util import spec_from_file_location, module_from_spec
HERE=Path(__file__).resolve().parent
def load(name, path):
    spec=spec_from_file_location(name,path)
    module=module_from_spec(spec); spec.loader.exec_module(module)
    return module
pedal=load("pedal",HERE.parent/"standalone-pedals/model.py")
v3=load("v3",HERE.parent/"standalone-pedals-v3/model.py")
WIDTH,DEPTH=246,245

def base():
    p=pedal.slab(WIDTH,DEPTH,7,11).translate((0,81,0))
    # Subtract the exact pedal hole pattern from the shared plate.
    template=v3.upper()
    holes=v3.blank().cut(template)
    p=p.cut(holes)
    # Raised rails remain away from the shoes and tie the mounting zones.
    for x in (-119,0,119):
        p=p.union(pedal.slab(5,218,5,2).translate((x,81,6)))
    for x in (-110,110):
        for y in (-26,148,193):
            p=p.cut(pedal.hole(x,y,-1,6.6,15))
    for center in (-61,61):
        for x in (-31,31):
            for y in (161,190):
                p=p.cut(pedal.hole(center+x,y,-1,5.5,10))
    return p

def carrier():
    # Lay flat to print. Attach it upright to two metal angle brackets.
    p=pedal.slab(81,53,6,5)
    p=p.cut(cq.Workplane("XY").rect(41.5,20.5).extrude(6))
    for x in (-24.75,24.75):
        for y in (-5,5):
            p=p.cut(pedal.hole(x,y,-1,3.4,8))
    for x in (-31,31):
        for y in (-18,18):
            p=p.cut(pedal.hole(x,y,-1,5.5,8))
    return p

if __name__=="__main__":
    for n,p in (("A1-ribbed-base",base()),("MG996R-upright-x2",carrier())):
        assert len(p.solids().vals())==1 and p.val().isValid()
        cq.exporters.export(p,str(HERE/f"{n}.stl"),tolerance=.08,angularTolerance=.12)
