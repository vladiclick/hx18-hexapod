from pathlib import Path
import sys,json,numpy as np
sys.modules["networkx"]=None
import trimesh
out=Path(__file__).resolve().parent.parent
manifest=json.loads((out/'Mesh-validation.json').read_text())
for p in manifest:
 m=trimesh.load_mesh(out/'STL'/(p['part']+'.stl'),process=True)
 assert m.is_watertight and m.is_winding_consistent and m.volume>0,p['part']
 assert np.allclose(m.extents,p['size_mm'],atol=.002),p['part']
 assert abs(m.bounds[0,2])<1e-5,p['part']
 assert abs(m.volume/1000-p['volume_cm3'])<.0001,p['part']
 parents=list(range(len(m.faces)))
 def find(x):
  while parents[x]!=x:parents[x]=parents[parents[x]];x=parents[x]
  return x
 for a,b in m.face_adjacency:parents[find(int(a))]=find(int(b))
 assert len({find(i) for i in range(len(parents))})==1,p['part']
print('17 STL verified; no files changed')
