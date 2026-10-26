"""Native joint graph, sampled motion and independent FK checks."""
import adsk.core,adsk.fusion,math,itertools,json,time
from v3_setup import setup

def audit(b):
 app=setup(b);root=b.ROOT;design=b.DESIGN
 rotations=[j for j in root.asBuiltJoints if j.jointMotion.jointType==adsk.fusion.JointTypes.RevoluteJointType]
 rotations.sort(key=lambda j:(int(j.name.split(' · ')[0][1:]),{'YAW':0,'HIP':1,'KNEE':2}[j.name.split(' · ')[1].split()[0]]))
 assert len(rotations)==3*b.LEG_COUNT
 labels={o.attributes.itemByName('Hexapod','AssemblyLabel').value:o for o in root.occurrences if o.attributes.itemByName('Hexapod','AssemblyLabel')}
 # Graph must be one grounded, connected, acyclic assembly.
 nodes={o.name:o for o in root.occurrences};parents={key:key for key in nodes}
 def find(k):
  while parents[k]!=k:k=parents[k]
  return k
 for j in root.asBuiltJoints:
  a,c=j.occurrenceOne.name,j.occurrenceTwo.name
  assert a in nodes and c in nodes
  x,y=find(a),find(c);assert x!=y,'Closed constraint cycle: '+j.name;parents[x]=y
 assert len(set(find(k) for k in nodes))==1
 assert sum(o.isGrounded for o in nodes.values())==1
 assert len(list(root.asBuiltJoints))==len(nodes)-1
 poses=[('neutral',[0.]*(3*b.LEG_COUNT))]
 for yaw,hip,knee in itertools.product((-20,0,20),(-12,0,12),(-15,0,15)):
  if (yaw,hip,knee)!=(0,0,0):poses.append((f'uniform {yaw},{hip},{knee}',[yaw,hip,knee]*b.LEG_COUNT))
 for n in range(b.LEG_COUNT):
  for axis,limit in enumerate((20,12,15)):
   for sign in (-1,1):
    p=[0.]*(3*b.LEG_COUNT);p[n*3+axis]=sign*limit;poses.append((f'leg{n+1} axis{axis+1} {sign}',p))
 for signs in itertools.product((-1,1),repeat=3):
  p=[]
  for n in range(b.LEG_COUNT):p.extend([signs[i]*(20,12,15)[i]*(1 if n%2==0 else -1) for i in range(3)])
  poses.append(('alternating '+str(signs),p))
 result={'status':'sampled geometric checks; no real actuator, load, wire or gait validation','build_revision':b.BUILD_REVISION,'poses_tested':0,'fk_points_tested':0,'max_fk_error_mm':0.,'max_midplane_error_mm':0.,'collisions':[],'graph':{'nodes':len(nodes),'edges':len(list(root.asBuiltJoints)),'grounded':1,'connected':True,'cycles':0},'joint_limits_degrees':{'yaw':[-20,20],'hip':[-12,12],'knee':[-15,15]},'samples':[]}
 try:
  for index,(name,values) in enumerate(poses):
   for j,v in zip(rotations,values):
    target=math.radians(v)
    if abs(j.jointMotion.rotationValue-target)>1e-10:j.jointMotion.rotationValue=target
   adsk.doEvents();design.computeAll()
   applied=[math.degrees(j.jointMotion.rotationValue) for j in rotations]
   errors=[]
   for n in range(b.LEG_COUNT):
    o=labels[f'L{n+1} tibia'];p=b.pt(93,0,0);p.transformBy(o.transform2)
    local=p.copy();inverse=labels[f'L{n+1} coxa'].transform2.copy();inverse.invert();local.transformBy(inverse)
    plane_error=abs(local.y*10);assert plane_error<1e-4,'Toe left common leg plane'
    result['max_midplane_error_mm']=max(result['max_midplane_error_mm'],plane_error)
    expected=b.geometry.foot(n*60,*applied[n*3:n*3+3])
    error=math.dist((p.x*10,p.y*10,p.z*10),expected);errors.append(error)
    assert error<1e-4,f'Independent FK mismatch {name}, leg{n+1}: {error}'
   collisions=b.interference()
   result['poses_tested']+=1;result['fk_points_tested']+=b.LEG_COUNT
   result['max_fk_error_mm']=max(result['max_fk_error_mm'],*errors)
   result['samples'].append({'pose':name,'angles_degrees':applied,'collisions':len(collisions)})
   if collisions:result['collisions'].append({'pose':name,'pairs':collisions})
   if index%8==0:b.log(f'Motion audit {index+1}/{len(poses)}, colliding poses {len(result["collisions"])}')
 finally:
  for j in rotations:
   if abs(j.jointMotion.rotationValue)>1e-10:j.jointMotion.rotationValue=0
  adsk.doEvents();design.computeAll()
  open(b.OUT+'/Motion-validation.json','w').write(json.dumps(result,indent=2))
 assert result['poses_tested']==len(poses)
 assert not result['collisions'],'Sampled shell collision'
 assert not b.interference(),'Neutral reset collision'
 b.log('MOTION AUDIT PASSED '+str(len(poses))+' poses')
