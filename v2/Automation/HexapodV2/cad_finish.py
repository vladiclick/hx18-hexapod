import adsk.core,adsk.fusion,math,json,os
OUT=os.path.abspath(os.path.join(os.path.dirname(__file__),'../..'))
BASE=OUT
os.makedirs(OUT+'/Automation/logs',exist_ok=True)
OUT=OUT+'/'
def finish():
 app=adsk.core.Application.get();d=adsk.fusion.Design.cast(app.activeProduct);root=d.rootComponent
 assert 'v2' in app.activeDocument.name
 cad=json.load(open(OUT+'CAD-validation.json'));motion=json.load(open(OUT+'Motion-validation.json'));gait=json.load(open(OUT+'Gait-validation.json'))
 assert not cad['neutral_interferences'] and not cad['timeline_issues']
 assert motion['tested_cases']==133 and motion['collision_cases']==0 and gait['collision_cases']==0
 for j in root.asBuiltJoints:
  if j.jointMotion.jointType==adsk.fusion.JointTypes.RevoluteJointType:assert abs(j.jointMotion.rotationValue)<1e-7
 d.activateRootComponent();app.activeViewport.visualStyle=adsk.core.VisualStyles.ShadedWithVisibleEdgesOnlyVisualStyle
 camera=app.activeViewport.camera;camera.viewOrientation=adsk.core.ViewOrientations.ArbitraryViewOrientation
 camera.eye=adsk.core.Point3D.create(28,-32,23);camera.target=adsk.core.Point3D.create(0,0,-1);camera.upVector=adsk.core.Vector3D.create(0,0,1);camera.isSmoothTransition=False;camera.isFitView=True;app.activeViewport.camera=camera
 adsk.doEvents();app.activeViewport.refresh()
 em=d.exportManager;assert em.execute(em.createFusionArchiveExportOptions(OUT+'HX18-MG90S.f3d'))
 step=em.createSTEPExportOptions(OUT+'HX18-MG90S.step');step.isIncludingInvisibleBodies=False;step.isIncludingInvisibleComponents=False;assert em.execute(step)
 old=app.activeDocument;doc=app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(OUT+'HX18-MG90S.f3d'));doc.name='HX18-MG90S v2 · integrated ESP32 core';d=adsk.fusion.Design.cast(app.activeProduct);root=d.rootComponent;d.activateRootComponent()
 report={'F3D_reopened':True,'occurrences':root.occurrences.count,'revolute_joints':0,'rigid_joints':0,'preserved_print_components':0,'original_reference_sketch_preserved':False,'timeline_issues':[]}
 for j in root.asBuiltJoints:
  if j.jointMotion.jointType==adsk.fusion.JointTypes.RevoluteJointType:
   report['revolute_joints']+=1;assert abs(j.jointMotion.rotationValue)<1e-7
   n=int(j.name[1:j.name.index(' ·')]);a=math.radians((n-1)*60)
   expected=adsk.core.Vector3D.create(0,0,1) if 'YAW' in j.name else adsk.core.Vector3D.create(-math.sin(a),math.cos(a),0)
   assert abs(j.jointMotion.rotationAxisVector.dotProduct(expected))>.9999
  else:report['rigid_joints']+=1
 seen=set()
 for o in root.occurrences:
  c=o.component
  if c.entityToken in seen:continue
  seen.add(c.entityToken)
  if c.attributes.itemByName('Hexapod','Print'):
   assert c.bRepBodies.count==1 and c.bRepBodies.item(0).isSolid
   assert abs(c.bRepBodies.item(0).volume-float(c.attributes.itemByName('Hexapod','RegisteredVolume').value))<1e-7
   report['preserved_print_components']+=1
 for s in root.sketches:
  if s.name.startswith('REFERENCE | original'):report['original_reference_sketch_preserved']=True;assert not s.isLightBulbOn
 for i in range(d.timeline.count):
  e=d.timeline.item(i)
  if e.healthState!=adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState:report['timeline_issues'].append(e.name)
 assert report['occurrences']==cad['occurrences'] and report['revolute_joints']==18 and report['rigid_joints']==cad['rigid_joints']
 assert report['preserved_print_components']==len(cad['print_parts']) and report['original_reference_sketch_preserved'] and not report['timeline_issues']
 visible=[o for o in root.occurrences if not o.component.name.startswith('FIT TEST')]
 mins=[min(o.boundingBox.minPoint.asArray()[i] for o in visible)*10 for i in range(3)];maxs=[max(o.boundingBox.maxPoint.asArray()[i] for o in visible)*10 for i in range(3)]
 report['assembly_bounds_mm']=[mins,maxs];report['assembly_size_mm']=[b-a for a,b in zip(mins,maxs)]
 open(OUT+'Round-trip-validation.json','w').write(json.dumps(report,indent=2));old.close(False);doc.activate()
 camera=app.activeViewport.camera;camera.eye=adsk.core.Point3D.create(28,-32,23);camera.target=adsk.core.Point3D.create(0,0,-1);camera.upVector=adsk.core.Vector3D.create(0,0,1);camera.isSmoothTransition=False;camera.isFitView=True;app.activeViewport.camera=camera
 app.activeViewport.saveAsImageFile(OUT+'HX18-preview.png',1800,1400)
 # Two honest CAD closeups: removable lid and upper saddle temporarily hidden.
 cap=next(o for o in root.occurrences if o.component.name=='CORE | CoreCap');bridge=next(o for o in root.occurrences if o.component.name=='CORE | CoreBridge')
 cap.isLightBulbOn=False;camera=app.activeViewport.camera;camera.eye=adsk.core.Point3D.create(12,-16,18);camera.target=adsk.core.Point3D.create(0,0,2.5);camera.isFitView=False;camera.viewExtents=7.5;app.activeViewport.camera=camera;adsk.doEvents()
 app.activeViewport.saveAsImageFile(OUT+'Core-electronics.png',1600,1200)
 bridge.isLightBulbOn=False
 feather=next(o for o in root.occurrences if 'BRAIN |' in o.component.name);logic=next(o for o in root.occurrences if 'D24V10' in o.component.name)
 feather.isLightBulbOn=False;logic.isLightBulbOn=False;adsk.doEvents();app.activeViewport.refresh();app.activeViewport.saveAsImageFile(OUT+'Core-PCA-power.png',1600,1200)
 for o in [cap,bridge,feather,logic]:o.isLightBulbOn=True
 camera=app.activeViewport.camera;camera.eye=adsk.core.Point3D.create(28,-32,23);camera.target=adsk.core.Point3D.create(0,0,-1);camera.upVector=adsk.core.Vector3D.create(0,0,1);camera.isFitView=True;app.activeViewport.camera=camera
 open(OUT+'/Automation/logs/v2-finish-complete','w').write('COMPLETE')
