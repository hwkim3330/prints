"""Compare rev2 print meshes with preserved original meshes; run after crab_lightening_experiment.py.
No strength or full motion-envelope certification is implied.
"""
from pathlib import Path
import json, trimesh, zipfile,re
root=Path(__file__).resolve().parent
report={}
expected = {"turret", "turntable", "upper_q", "upper_qp", "fore_f", "fore_fp", "claw", "dactyl", "spacer_upper", "spacer_fore", "coupon"}
assert {p.stem for p in (root/'rev2').glob('*.stl')} == expected
changed = {"upper_qp", "fore_fp", "claw"}
for p in sorted((root/'rev2').glob('*.stl')):
 m=trimesh.load(p,force='mesh'); old=trimesh.load(root/p.name,force='mesh')
 assert m.is_volume,p.name
 assert max(abs(m.extents[:2]-old.extents[:2]))<0.01,p.name
 if p.stem in changed:
  assert m.volume<old.volume,p.name
  assert len(m.split())==1,p.name
 else:
  assert abs(m.volume-old.volume)<0.01,p.name
 assert (m.extents[:2]<240).all(),p.name
 assert abs(m.bounds[0,2])<1e-4,p.name
 flat=(m.face_normals[:,2]<-.999)&(m.triangles_center[:,2]<.01)
 assert m.area_faces[flat].sum()>20,p.name
 down=(m.face_normals[:,2]<-.57)&(m.triangles_center[:,2]>.21)
 olddown=(old.face_normals[:,2]<-.57)&(old.triangles_center[:,2]>.21)
 report[p.name]={'solid_cm3_old':round(old.volume/1000,3),'solid_cm3_new':round(m.volume/1000,3),'volume_reduction_percent':round((1-m.volume/old.volume)*100,2),'shells':len(m.split()),'bed_contact_mm2':round(m.area_faces[flat].sum(),1),'downward_area_mm2':round(m.area_faces[down].sum(),1),'old_downward_area_mm2':round(old.area_faces[olddown].sum(),1)}
 assert report[p.name]['downward_area_mm2']<=report[p.name]['old_downward_area_mm2']+1,p.name
print(json.dumps(report,indent=2))
(root/'rev2'/'validation.json').write_text(json.dumps(report,indent=2))
