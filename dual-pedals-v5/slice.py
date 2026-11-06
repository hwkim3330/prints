import subprocess,concurrent.futures,json,zipfile,re,shutil
from pathlib import Path
O=Path(__file__).resolve().parent; W=O/'slice-work'; W.mkdir(exist_ok=True)
def run(n):
 d=W/n;d.mkdir(exist_ok=True)
 profile=O/'A1-PETG-process.json'
 if n=='A-base':
  cfg=json.loads(profile.read_text());cfg.update(brim_width='0',brim_type='no_brim');cfg['enable_support']='0' if n=='A-base' else '1';profile=d/'process.json';profile.write_text(json.dumps(cfg))
 cmd=['/Applications/BambuStudio.app/Contents/MacOS/BambuStudio','--load-settings',str(O/'A1-machine.json')+';'+str(profile),'--load-filaments',str(O/'Generic-PETG-filament.json'),'--orient','0','--arrange','1','--ensure-on-bed','--slice','0','--outputdir',str(d),'--export-3mf',n+'-PETG.gcode.3mf',str(O/(n+'.stl'))]
 with open(d/'slice.log','w') as f:r=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT)
 print(n,r.returncode,flush=True)
 if r.returncode==0:shutil.copy2(d/(n+'-PETG.gcode.3mf'),O/(n+'-PETG.gcode.3mf'))
 return n,r.returncode
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex: results=list(ex.map(run,['D-fit-coupon','A-base','B-pedals','C-hardware','E-carriers']))
(O/'slice-status.json').write_text(json.dumps(results,indent=2))
