"""Reopen the actual native archive and inspect saved assembly, then capture views."""
import adsk.core, adsk.fusion, json, math

def verify(b):
 app=adsk.core.Application.get()
 path=b.OUT+'/'
 options=app.importManager.createFusionArchiveImportOptions(path+'HX18-Inline-V5-Concept.f3d')
 doc=app.importManager.importToNewDocument(options)
 assert doc, 'Archive import failed'
 doc.activate();doc.name="HX18 · INLINE V5 · verified archive"
 design=adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
 assert design
 b.DESIGN=design;b.ROOT=design.rootComponent
 root=b.ROOT;design.activateRootComponent();app.userInterface.activeSelections.clear()
 joints=list(root.asBuiltJoints)
 prints={}
 for o in root.occurrences:
  c=o.component;a=c.attributes.itemByName('Hexapod','Print')
  if a:prints[c.bRepBodies.item(0).name]=dict(json.loads(a.value), volume_cm3=c.bRepBodies.item(0).volume, bodies=c.bRepBodies.count, solid=c.bRepBodies.item(0).isSolid)
 data={'reopened_actual_archive':True,'occurrences':root.occurrences.count,'revolute_joints':sum(j.jointMotion.jointType==adsk.fusion.JointTypes.RevoluteJointType for j in joints),'rigid_joints':sum(j.jointMotion.jointType==adsk.fusion.JointTypes.RigidJointType for j in joints),'print_definitions':prints,'timeline_issues':[],'neutral_interferences':b.interference()}
 for i in range(design.timeline.count):
  t=design.timeline.item(i)
  if t.healthState!=adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState:data['timeline_issues'].append({'index':i,'name':t.name})
 open(path+'Archive-roundtrip.json','w').write(json.dumps(data,indent=2))
 assert data['occurrences']==12+9*b.LEG_COUNT and data['revolute_joints']==3*b.LEG_COUNT and data['rigid_joints']==11+6*b.LEG_COUNT
 assert len(prints)==8 and all(x['bodies']==1 and x['solid'] for x in prints.values())
 assert not data['timeline_issues'] and not data['neutral_interferences']
 vp=app.activeViewport;vp.visualStyle=adsk.core.VisualStyles.ShadedVisualStyle
 visibility={o.name:o.isLightBulbOn for o in root.occurrences}
 def shot(filename,eye,target=(0,0,-10),up=(0,0,1)):
  app.userInterface.activeSelections.clear()
  camera=vp.camera;camera.viewOrientation=adsk.core.ViewOrientations.ArbitraryViewOrientation
  camera.eye=b.pt(*eye);camera.target=b.pt(*target);camera.upVector=b.V(*up)
  camera.isSmoothTransition=False;camera.isFitView=True;vp.camera=camera;vp.refresh();adsk.doEvents()
  assert vp.saveAsImageFile(path+filename,1800,1400)
 try:
  shot('HX18-Inline-V5-preview.png',(300,-330,230))
  for o in root.occurrences:
   label=o.attributes.itemByName('Hexapod','AssemblyLabel')
   keep=(label and label.value.startswith('L1 ')) or o.component.name.startswith('SERVICE HARDWARE | L1 ')
   o.isLightBulbOn=bool(keep)
  shot('V5-One-leg.png',(230,260,130),target=(110,0,-5))
  shot('V5-One-leg-front.png',(110,320,-5),target=(110,0,-5))
  shot('V5-One-leg-rear.png',(110,-320,-5),target=(110,0,-5))
  shot('V5-One-leg-edge.png',(350,0,-5),target=(110,0,-5))
  for o in root.occurrences:o.isLightBulbOn=visibility[o.name]
  shot('HX18-Top.png',(0,0,350),up=(0,1,0))
  shot('HX18-Underside.png',(260,-300,-260),up=(0,0,-1))
  for o in root.occurrences:
   name=o.component.name
   if name.startswith('LEG |') or name.startswith('FOOT |') or name=='CORE | CoreLid' or name.startswith('SERVICE HARDWARE | L') or 'HipReserve' in name or 'KneeReserve' in name:o.isLightBulbOn=False
  shot('HX18-Core-open.png',(180,-220,240),target=(0,0,-13))
 finally:
  for o in root.occurrences:o.isLightBulbOn=visibility[o.name]
  shot('HX18-Inline-V5-preview.png',(300,-330,230))
 b.log('ARCHIVE ROUNDTRIP AND NATIVE VIEWS PASSED')
