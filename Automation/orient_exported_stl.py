from pathlib import Path
import json, math, shutil
import numpy as np
import sys
sys.modules["networkx"]=None
import trimesh
OUT=Path(__file__).resolve().parent.parent
BASE=OUT
report=json.loads((OUT/'CAD-validation.json').read_text())
raw=OUT/'Automation/logs/raw-STL';raw.mkdir(parents=True,exist_ok=True)
def components(m):
 parent=list(range(len(m.faces)))
 def find(x):
  while parent[x]!=x:
   parent[x]=parent[parent[x]];x=parent[x]
  return x
 for a,b in m.face_adjacency:
  a,b=find(int(a)),find(int(b));parent[a]=b
 return len({find(i) for i in range(len(parent))})
results=[]
for part in report['print_parts']:
 name=part['part'];path=OUT/'STL'/f'{name}.stl'
 shutil.copy2(path,raw/path.name)
 m=trimesh.load_mesh(path,process=True)
 assert m.is_watertight and m.is_winding_consistent and m.volume>0,name
 assert components(m)==1,name+' disconnected mesh'
 assert abs(m.volume/1000-part['volume_cm3'])/part['volume_cm3']<0.002,name+' units or volume mismatch'
 axis=part['print_bed_normal']
 if axis in ['y','-y']:
  m.apply_transform(trimesh.transformations.rotation_matrix(math.pi/2*(1 if axis=='y' else -1),[1,0,0]))
 minimum=m.bounds[0];m.apply_translation(-minimum)
 assert abs(m.bounds[0,2])<1e-5
 m.export(path)
 results.append({'part':name,'quantity':part['quantity'],'watertight':bool(m.is_watertight),'connected_solids':components(m),'size_mm':m.extents.round(3).tolist(),'volume_cm3':round(m.volume/1000,5),'bed_z_min_mm':float(m.bounds[0,2])})
(OUT/'Mesh-validation.json').write_text(json.dumps(results,indent=2))
print(json.dumps(results,indent=2))
