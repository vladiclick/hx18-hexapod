import adsk.core,adsk.fusion,math,json,itertools,os,csv,hashlib
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
  applied=[[math.degrees(j.jointMotion.rotationValue) for j in g] for g in groups]
  quantization=max(abs(a-b) for va,vb in zip(applied,vectors) for a,b in zip(va,vb));assert quantization<=.050001
  errs=[]
  for n,(o,angles) in enumerate(zip(tibias,applied)):
   yaw,hip,knee=angles;a=math.radians(n*60);theta=math.radians(n*60-yaw);fa=math.radians(-25+hip);ta=math.radians(-95+hip+knee)
   x=30+42*math.cos(fa)+80*math.cos(ta);expected=[49*math.cos(a)+x*math.cos(theta)-13.5*math.sin(theta),49*math.sin(a)+x*math.sin(theta)+13.5*math.cos(theta),38+42*math.sin(fa)+80*math.sin(ta)]
   p=adsk.core.Point3D.create(8,1.35,0);p.transformBy(o.transform2);errs.append(math.dist(expected,[v*10 for v in p.asArray()]))
  assert max(errs)<1e-4, str({'errors':errs,'requested':vectors,'actual':[[math.degrees(j.jointMotion.rotationValue) for j in g] for g in groups]})
  report['cases'].append({'label':label,'offset_degrees':vectors,'collisions':collisions,'max_kinematics_error_mm':max(errs),'native_applied_offset_degrees':applied,'max_native_angle_rounding_deg':quantization})
  open(OUT+'Gait-validation.json','w').write(json.dumps(report,indent=2))
  with open(OUT+'/Automation/logs/v2-gait-progress.txt','a') as f:f.write(label+' collisions='+str(len(collisions))+'\n')
 open(OUT+'/Automation/logs/v2-gait-progress.txt','w').write('Start\n')
 report['sources']=[]
 try:
  for name,stride in [('gait-targets.csv',3),('startup-targets.csv',6)]:
   path=OUT+'/Firmware/'+name
   raw=open(path,'rb').read();rows=list(csv.DictReader(raw.decode().splitlines()));frames={}
   for row in rows:frames.setdefault(float(row['seconds']),[]).append(row)
   times=sorted(frames);selected=set(range(0,len(times),stride));selected.add(len(times)-1)
   # Add exact angle extrema to the uniform120ms samples.
   for leg in range(1,7):
    for axis in ['yaw_deg','hip_deg','knee_deg']:
     vals=[float(next(r for r in frames[t] if int(r['leg'])==leg)[axis]) for t in times]
     selected.add(min(range(len(vals)),key=lambda i:vals[i]));selected.add(max(range(len(vals)),key=lambda i:vals[i]))
   report['sources'].append({'file':name,'sha256':hashlib.sha256(raw).hexdigest(),'csv_frames':len(times),'selected_frames':len(selected),'uniform_interval_ms':round((times[stride]-times[0])*1000,6),'exact_joint_extrema_included':True})
   for i in sorted(selected):
    t=times[i];frame=sorted(frames[t],key=lambda r:int(r['leg']));assert len(frame)==6
    vectors=[[float(r[k]) for k in ['yaw_deg','hip_deg','knee_deg']] for r in frame]
    check(name+':'+str(t),vectors)
    errors=[]
    for n,(o,r) in enumerate(zip(tibias,frame)):
     a=math.radians(n*60);x=float(r['x_mm']);y=float(r['y_mm']);z=float(r['z_mm']);expected=[49*math.cos(a)+x*math.cos(a)-y*math.sin(a),49*math.sin(a)+x*math.sin(a)+y*math.cos(a),38+z]
     p=adsk.core.Point3D.create(8,1.35,0);p.transformBy(o.transform2);errors.append(math.dist(expected,[v*10 for v in p.asArray()]))
    report['cases'][-1]['max_firmware_target_error_mm']=max(errors)
    assert max(errors)<.3,'CSV foot target differs beyond native0.1degree solver rounding'
    report['firmware_target_tolerance_mm']=.3;report['native_joint_angle_resolution_deg']=.1
 finally:drive([[0,0,0]]*6)
 report['maximum_firmware_target_error_mm']=max(c['max_firmware_target_error_mm'] for c in report['cases'])
 report['tested_cases']=len(report['cases']);report['collision_cases']=sum(bool(c['collisions']) for c in report['cases']);report['kinematics_comparisons']=len(report['cases'])*6;report['maximum_kinematics_error_mm']=max(c['max_kinematics_error_mm'] for c in report['cases'])
 open(OUT+'Gait-validation.json','w').write(json.dumps(report,indent=2))
 camera=app.activeViewport.camera;camera.viewOrientation=adsk.core.ViewOrientations.ArbitraryViewOrientation
 camera.eye=adsk.core.Point3D.create(28,-32,23);camera.target=adsk.core.Point3D.create(0,0,-1);camera.upVector=adsk.core.Vector3D.create(0,0,1);camera.isSmoothTransition=False;camera.isFitView=True;app.activeViewport.camera=camera
 app.activeViewport.saveAsImageFile(OUT+'HX18-preview.png',1800,1400)
 with open(OUT+'/Automation/logs/v2-gait-progress.txt','a') as f:f.write('COMPLETE\n')
