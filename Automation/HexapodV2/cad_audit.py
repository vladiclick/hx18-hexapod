import adsk.core,adsk.fusion,math,json,itertools,os
OUT=os.path.abspath(os.path.join(os.path.dirname(__file__),'../..'))
BASE=OUT
os.makedirs(OUT+'/Automation/logs',exist_ok=True)
OUT=OUT+'/'
def run_audit():
 app=adsk.core.Application.get();d=adsk.fusion.Design.cast(app.activeProduct);root=d.rootComponent
 assert 'v2' in app.activeDocument.name
 report={'mode':'Sampled native CAD collision analysis; no continuous collision proof','cases':[]}
 joints={j.name:j for j in root.asBuiltJoints};groups=[[joints[f'L{n} · 01 COXA YAW'],joints[f'L{n} · 02 FEMUR PITCH'],joints[f'L{n} · 03 KNEE PITCH']] for n in range(1,7)]
 nodes=[o for o in root.occurrences if not o.component.name.startswith('FIT TEST')]
 grounded=[o for o in nodes if o.isGrounded];assert len(grounded)==1
 baseline=grounded[0].transform2.asArray();edges=[(j.occurrenceOne.entityToken,j.occurrenceTwo.entityToken) for j in joints.values()]
 assert len(edges)==len(nodes)-1
 visited={grounded[0].entityToken}
 while True:
  nxt=visited|{v for a,b in edges for u,v in [(a,b),(b,a)] if u in visited}
  if nxt==visited:break
  visited=nxt
 assert visited=={o.entityToken for o in nodes}
 report['joint_graph']={'visible_occurrences':len(nodes),'grounded':1,'constraints':len(edges),'connected':True,'cycles':False,'actuated_DOF':18}
 tibias=[next(o for o in nodes if o.attributes.itemByName('Hexapod','AssemblyLabel') and o.attributes.itemByName('Hexapod','AssemblyLabel').value==f'L{n} tibia') for n in range(1,7)]
 report['joint_axes']=[{'name':j.name,'axis':j.jointMotion.rotationAxisVector.asArray()} for g in groups for j in g]
 def drive(vectors):
  for g,vec in zip(groups,vectors):
   for j,v in zip(g,vec):j.jointMotion.rotationValue=math.radians(v)
  adsk.doEvents()
 def check(label,vectors):
  drive(vectors);ents=adsk.core.ObjectCollection.create()
  for o in root.occurrences:
   if not o.component.name.startswith('FIT TEST'):ents.add(o)
  inp=d.createInterferenceInput(ents);inp.areCoincidentFacesIncluded=False
  collisions=[]
  for r in d.analyzeInterference(inp):
   if r.interferenceBody.volume>1e-7:collisions.append({'a':r.entityOne.parentComponent.name,'b':r.entityTwo.parentComponent.name,'volume_mm3':r.interferenceBody.volume*1000})
  assert max(abs(a-b) for a,b in zip(baseline,grounded[0].transform2.asArray()))<1e-8
  errs=[]
  for n,(o,angles) in enumerate(zip(tibias,vectors)):
   yaw,hip,knee=angles;a=math.radians(n*60);theta=math.radians(n*60-yaw);fa=math.radians(-25+hip);ta=math.radians(-95+hip+knee)
   x=30+42*math.cos(fa)+80*math.cos(ta);expected=[49*math.cos(a)+x*math.cos(theta)-13.5*math.sin(theta),49*math.sin(a)+x*math.sin(theta)+13.5*math.cos(theta),38+42*math.sin(fa)+80*math.sin(ta)]
   p=adsk.core.Point3D.create(8,1.35,0);p.transformBy(o.transform2);errs.append(math.dist(expected,[v*10 for v in p.asArray()]))
  assert max(errs)<1e-4
  report['cases'].append({'label':label,'offset_degrees':vectors,'collisions':collisions,'max_kinematics_error_mm':max(errs)})
  open(OUT+'Motion-validation.json','w').write(json.dumps(report,indent=2))
  with open(OUT+'/Automation/logs/v2-audit-progress.txt','a') as f:f.write(label+' collisions='+str(len(collisions))+'\n')
 open(OUT+'/Automation/logs/v2-audit-progress.txt','w').write('Start\n')
 try:
  for yaw,hip,knee in itertools.product([-25,-12.5,0,12.5,25],[-15,-7.5,0,7.5,15],[-15,-7.5,0,7.5,15]):check(f'all:{yaw},{hip},{knee}',[[yaw,hip,knee]]*6)
  for yaw,hip,knee in itertools.product([-25,25],[-15,15],[-15,15]):check(f'alternating:{yaw},{hip},{knee}',[[yaw*(1 if n%2==0 else -1),hip,knee] for n in range(6)])
 finally:drive([[0,0,0]]*6)
 report['tested_cases']=len(report['cases']);report['collision_cases']=sum(bool(c['collisions']) for c in report['cases']);report['kinematics_comparisons']=len(report['cases'])*6;report['maximum_kinematics_error_mm']=max(c['max_kinematics_error_mm'] for c in report['cases'])
 open(OUT+'Motion-validation.json','w').write(json.dumps(report,indent=2))
 camera=app.activeViewport.camera;camera.viewOrientation=adsk.core.ViewOrientations.ArbitraryViewOrientation
 camera.eye=adsk.core.Point3D.create(28,-32,23);camera.target=adsk.core.Point3D.create(0,0,-1);camera.upVector=adsk.core.Vector3D.create(0,0,1);camera.isSmoothTransition=False;camera.isFitView=True;app.activeViewport.camera=camera
 app.activeViewport.saveAsImageFile(OUT+'HX18-preview.png',1800,1400)
 with open(OUT+'/Automation/logs/v2-audit-progress.txt','a') as f:f.write('COMPLETE\n')
