"""Single printed drum with direct six-arm horn seat. Bench prototype."""
from pathlib import Path
from importlib.util import spec_from_file_location,module_from_spec
import trimesh
HERE=Path(__file__).resolve().parent
spec=spec_from_file_location("horn",HERE.parent/"g923-horn/model.py")
h=module_from_spec(spec);spec.loader.exec_module(h)
# Thick hub plate provides blind pilot depth above the horn pocket.
BASE=7
PITCH_RADIUS=9  # A4 option 01 middle hole; confirm on actual horn.
def drum():
    p=h.disc(22,BASE)-h.horn_pocket()
    p+=h.disc(15,8,BASE-.1)
    p+=h.M.cylinder(3.8,15,18.8,circular_segments=96).translate((0,0,BASE+4.1))
    p+=h.disc(18.8,2.6,BASE+7.8)
    p-=h.disc(4.8,20,-1).rotate((0,0,1.7))
    for a in (0,120,240):
        p-=h.hole(.8,6.8,a,PITCH_RADIUS)
    p-=h.hole(1.35,21,90,16.3)
    return p
if __name__=="__main__":
    p=drum().rotate((180,0,0)).translate((0,0,17.4))
    data=p.to_mesh()
    mesh=trimesh.Trimesh(data.vert_properties[:,:3],data.tri_verts)
    assert mesh.is_volume and len(p.decompose())==1
    mesh.export(HERE/"6-arm-direct-drum-x2.stl")
