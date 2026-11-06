from pathlib import Path
import tempfile
import numpy as np
import trimesh
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgb
import model as cad
O=Path(__file__).resolve().parent
class Adapter:pass
m=Adapter()
def mesh(s):
 with tempfile.NamedTemporaryFile(suffix='.stl') as f:
  cad.cq.exporters.export(s,f.name,tolerance=.18,angularTolerance=.25)
  return trimesh.load(f.name)
m.mesh=mesh
# Self-contained z-buffer renderer.
def render(ax, parts, azimuth, elev):
 a,e=np.radians((azimuth,elev));right=np.array([-np.sin(a),np.cos(a),0]);near=np.array([np.cos(a)*np.cos(e),np.sin(a)*np.cos(e),np.sin(e)]);up=np.cross(near,right)
 tris=[];normals=[];palette=[]
 for solid,color in parts:
  me=mesh(solid);mask=me.face_normals@near>1e-6
  tris.extend(me.triangles[mask]);normals.extend(me.face_normals[mask]);palette.extend([to_rgb(color)]*mask.sum())
 tris,normals,palette=map(np.array,(tris,normals,palette));proj=np.stack((tris@right,-(tris@up),tris@near),axis=-1)
 low,high=proj[:,:,:2].min((0,1)),proj[:,:,:2].max((0,1));scale=1000/(high-low).max();proj[:,:,:2]=(proj[:,:,:2]-low)*scale+6
 w,h=np.ceil((high-low)*scale+12).astype(int);pixels=np.full((h,w,3),(242,243,245),dtype=np.uint8);zbuf=np.full((h,w),-np.inf)
 colors=np.clip((.59+.41*np.maximum(0,normals@np.array([.28,-.44,.85])))[:,None]*palette*255,0,255).astype(np.uint8)
 for tri,color in zip(proj,colors):
  lo=np.floor(tri[:,:2].min(0)).astype(int);hi=np.ceil(tri[:,:2].max(0)).astype(int)+1;a,b,c=tri;u,v=b-a,c-a;det=u[0]*v[1]-u[1]*v[0]
  if abs(det)<1e-8:continue
  yy,xx=np.ogrid[lo[1]:hi[1],lo[0]:hi[0]];x,y=xx+.5-a[0],yy+.5-a[1];b1=(x*v[1]-y*v[0])/det;b2=(y*u[0]-x*u[1])/det;zz=a[2]+b1*u[2]+b2*v[2];sub=zbuf[lo[1]:hi[1],lo[0]:hi[0]];mask=(b1>=0)&(b2>=0)&(b1+b2<=1)&(zz>sub);sub[mask]=zz[mask];pixels[lo[1]:hi[1],lo[0]:hi[0]][mask]=color
 ax.imshow(pixels);ax.axis('off')
colors=dict(base='#535f69',pedal='#e2e4e5',cheek='#8796a1',carrier='#8796a1',servo='#303842',arm='#2a9d8f',bearing='#aaaeb7',axle='#aaaeb7')
fig,axs=plt.subplots(1,2,figsize=(13,6),facecolor='#f2f3f5')
for ax,ang in zip(axs,(18,4)):
 render(ax,[(p,colors[n]) for n,p in cad.assembly(ang)],-58,35)
 ax.set_title('DUAL PEDALS / '+('REST 18 deg' if ang==18 else 'PRESSED 4 deg'),loc='left',fontweight='bold')
fig.text(.05,.02,'PETG prototype | rolling one-way contact | springs / fasteners omitted in this view | hardware fit untested',fontsize=10)
fig.savefig(O/'assembly.png',dpi=145,bbox_inches='tight');plt.close(fig)
fig,ax=plt.subplots(figsize=(9,7),facecolor='#f2f3f5')
ps=[]
for name,shape in cad.assembly(18):
 dz=dict(base=0,pedal=90,cheek=35,carrier=30,servo=50,arm=70,bearing=90,axle=35)[name]
 ps.append((shape.translate((0,0,dz)),colors[name]))
render(ax,ps,-58,32);ax.set_title('ASSEMBLY ORDER / EXPLODED',loc='left',fontweight='bold');fig.savefig(O/'exploded.png',dpi=145,bbox_inches='tight')
