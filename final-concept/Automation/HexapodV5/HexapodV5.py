import adsk.core, adsk.fusion, math, traceback, json, os, sys, time
OUT=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),'generated')
os.makedirs(OUT,exist_ok=True)
BUILD_REVISION='V5-inline-6'
LEG_COUNT=6
BASE_ROOT=os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
SOURCE_DIR=os.path.dirname(__file__)
sys.path.insert(0,SOURCE_DIR)
# Fusion retains Python modules between scripts: discard only foreign revisions.
for helper in ('v3_geometry','v3_setup','v3_audit','v3_verify','v3_core_layout','v4_shapes','core_enclosure','leg_shells','v5_layout'):
 loaded=sys.modules.get(helper)
 if loaded and os.path.realpath(getattr(loaded,'__file__',''))!=os.path.realpath(os.path.join(SOURCE_DIR,helper+'.py')):
  del sys.modules[helper]
import v3_geometry as geometry, importlib
importlib.reload(geometry)
from v3_geometry import DEFAULT, transform, position, stance, capsule
import v4_shapes
P=adsk.core.Point3D.create
V=adsk.core.Vector3D.create
VI=adsk.core.ValueInput.createByReal
F=adsk.fusion.FeatureOperations
ROOT=None
DESIGN=None
PARTS={}
PRINTS=[]
JOINTS=[]
FASTENERS=[]
def log(s):
 with open(os.path.join(OUT,'Progress.log'),'a') as f:f.write(s+'\n')
 adsk.doEvents()
def pt(x,y,z):return P(x/10,y/10,z/10)
def matrix(yaw,pitch,origin,servo=False):
 a=transform(yaw,pitch,origin)
 if servo:
  a=[[r[0],-servo*r[2],servo*r[1],r[3]] for r in a[:3]]+[[0,0,0,1]]
 m=adsk.core.Matrix3D.create()
 m.setWithCoordinateSystem(pt(*origin),V(*[a[r][0] for r in range(3)]),V(*[a[r][1] for r in range(3)]),V(*[a[r][2] for r in range(3)]))
 probe=P(0,0,0);probe.transformBy(m);assert probe.distanceTo(pt(*origin))<1e-8
 return m
def component(name):
 o=ROOT.occurrences.addNewComponent(adsk.core.Matrix3D.create());o.component.name=name
 return o

def sketch(c,axis,offset,name):
 plane={'z':c.xYConstructionPlane,'y':c.xZConstructionPlane,'x':c.yZConstructionPlane}[axis]
 normal={'z':plane.geometry.normal.z,'y':plane.geometry.normal.y,'x':plane.geometry.normal.x}[axis]
 if offset:
  i=c.constructionPlanes.createInput();i.setByOffset(plane,VI(offset/10/normal))
  plane=c.constructionPlanes.add(i);plane.name=name+' plane';plane.isLightBulbOn=False
 s=c.sketches.add(plane);s.name=name
 return s

def mappt(s,axis,offset,a):
 coords={'z':(a[0],a[1],offset),'y':(a[0],offset,a[1]),'x':(offset,a[0],a[1])}[axis]
 return s.modelToSketchSpace(pt(*coords))

def profile(c,axis,offset,loops,name):
 s=sketch(c,axis,offset,name);s.isComputeDeferred=True
 for kind,data in loops:
  if kind=='circle':
   x,y,r=data;s.sketchCurves.sketchCircles.addByCenterRadius(mappt(s,axis,offset,(x,y)),r/10)
  elif kind=='arcs':
   for segment,coords in data:
    points=[mappt(s,axis,offset,a) for a in coords]
    if segment=='line':s.sketchCurves.sketchLines.addByTwoPoints(*points)
    else:s.sketchCurves.sketchArcs.addByThreePoints(*points)
  else:
   pts=[mappt(s,axis,offset,a) for a in data]
   for i in range(len(pts)):s.sketchCurves.sketchLines.addByTwoPoints(pts[i],pts[(i+1)%len(pts)])
 s.isComputeDeferred=False
 assert s.profiles.count>0,name+' has no closed profile'
 return s

def extrude(c,axis,offset,loops,depth,op,name):
 s=profile(c,axis,offset,loops,name)
 collection=adsk.core.ObjectCollection.create()
 for p in s.profiles:collection.add(p)
 i=c.features.extrudeFeatures.createInput(collection,op)
 normal={'z':s.referencePlane.geometry.normal.z,'y':s.referencePlane.geometry.normal.y,'x':s.referencePlane.geometry.normal.x}[axis]
 i.setDistanceExtent(False,VI(depth/10/normal))
 if op==F.CutFeatureOperation:i.participantBodies=[b for b in c.bRepBodies]
 e=c.features.extrudeFeatures.add(i);e.name=name;s.isLightBulbOn=False
 return e

def rect(x0,y0,x1,y1):return ('poly',[(x0,y0),(x1,y0),(x1,y1),(x0,y1)])
def circ(x,y,r):return ('circle',(x,y,r))
def cap(a,b,r):return ('arcs',v4_shapes.capsule_entities(a,b,r))
def roundrect(x0,y0,x1,y1,r):return ('arcs',v4_shapes.rounded_rect_entities(x0,y0,x1,y1,r))
def poly(points):return ('poly',points)
def add(c,axis,off,loops,d,name):
 return extrude(c,axis,off,loops,d,F.JoinFeatureOperation if c.bRepBodies.count else F.NewBodyFeatureOperation,name)
def cut(c,axis,off,loops,d,name):return extrude(c,axis,off,loops,d,F.CutFeatureOperation,name)

def cone_loft(c,axis,x,y,levels,operation,name):
 i=c.features.loftFeatures.createInput(operation)
 for offset,radius in levels:
  s=profile(c,axis,offset,[circ(x,y,radius)],name+' section')
  i.loftSections.add(s.profiles.item(0));s.isLightBulbOn=False
 if operation==F.CutFeatureOperation:i.participantBodies=[b for b in c.bRepBodies]
 e=c.features.loftFeatures.add(i);e.name=name;return e

def loft(c,axis,sections,operation,name):
 i=c.features.loftFeatures.createInput(operation)
 for off,loop in sections:
  s=profile(c,axis,off,[loop],name+' section')
  i.loftSections.add(s.profiles.item(0));s.isLightBulbOn=False
 if operation==F.CutFeatureOperation:i.participantBodies=[b for b in c.bRepBodies]
 e=c.features.loftFeatures.add(i);e.name=name;return e

def color(c,rgb):
 a=DESIGN.appearances.itemByName('HX '+str(rgb))
 if not a:
  source=None
  for lib in adsk.core.Application.get().materialLibraries:
   for candidate in lib.appearances:
    if 'plastic' in candidate.name.lower() and 'matte' in candidate.name.lower():
     source=candidate;break
   if source:break
  if not source:return
  a=DESIGN.appearances.addByCopy(source,'HX '+str(rgb))
  prop=adsk.core.ColorProperty.cast(a.appearanceProperties.itemById('opaque_albedo'))
  if prop:prop.value=adsk.core.Color.create(*rgb,255)
 for b in c.bRepBodies:b.appearance=a

def register(o,key,qty,axis='z',bed=0):
 c=o.component
 assert c.bRepBodies.count==1,key+' disconnected bodies'
 b=c.bRepBodies.item(0);b.name=key
 assert b.isSolid and b.volume>0,key+' invalid solid'
 c.attributes.add('Hexapod','RegisteredVolume',str(b.volume))
 c.attributes.add('Hexapod','Print',json.dumps({'quantity':qty,'bed_normal':axis,'bed_offset_mm':bed}))
 PARTS[key]=o;PRINTS.append((key,c,qty,axis,bed));color(c,(220,224,225) if key in ['CoxaCarrier','CoxaCheek','FemurCarrier','FemurCheek','Tibia'] else (44,48,51))
 log('Built '+key)

def rigid(a,b,name):
 i=ROOT.asBuiltJoints.createInput(a,b,None);i.setAsRigidJointMotion()
 j=ROOT.asBuiltJoints.add(i);j.name=name;j.isLightBulbOn=False;JOINTS.append(j);return j

def revolute(a,b,point,axis,name,limits):
 # JointGeometry determines the actual frame; a custom axis alone is ignored by some Fusion builds.
 s=ROOT.sketches.add(ROOT.xYConstructionPlane);s.name=name+' plane anchors';s.is3D=True
 u=(1,0,0) if abs(axis[2])>0.9 else (0,0,1)
 v=(axis[1]*u[2]-axis[2]*u[1],axis[2]*u[0]-axis[0]*u[2],axis[0]*u[1]-axis[1]*u[0])
 anchors=[s.sketchPoints.add(s.modelToSketchSpace(pt(*(point[i]+direction[i]*10 for i in range(3))))) for direction in [(0,0,0),u,v]]
 pi=ROOT.constructionPlanes.createInput();pi.setByThreePoints(*anchors)
 plane=ROOT.constructionPlanes.add(pi);plane.name=name+' joint frame';plane.isLightBulbOn=False
 circle_sketch=ROOT.sketches.add(plane);circle_sketch.name=name+' axis profile'
 circle_sketch.sketchCurves.sketchCircles.addByCenterRadius(circle_sketch.modelToSketchSpace(pt(*point)),0.1)
 geo=adsk.fusion.JointGeometry.createByProfile(circle_sketch.profiles.item(0),None,adsk.fusion.JointKeyPointTypes.CenterKeyPoint)
 ji=ROOT.asBuiltJoints.createInput(a,b,geo)
 ji.setAsRevoluteJointMotion(adsk.fusion.JointDirections.ZAxisJointDirection)
 j=ROOT.asBuiltJoints.add(ji);j.name=name
 s.isLightBulbOn=False;circle_sketch.isLightBulbOn=False
 motion=adsk.fusion.RevoluteJointMotion.cast(j.jointMotion)
 expected=V(*axis);actual=motion.rotationAxisVector
 assert abs(actual.dotProduct(expected))>0.9999,name+' incorrect axis'
 lim=motion.rotationLimits;lim.minimumValue=math.radians(limits[0]);lim.maximumValue=math.radians(limits[1]);lim.isMinimumValueEnabled=True;lim.isMaximumValueEnabled=True
 j.isLightBulbOn=False;JOINTS.append(j);return j

def assemble():
 chassis=PARTS['CoreTub'];chassis.isGrounded=True
 for key in ('CoreLid','ElectronicsCassette'):rigid(chassis,PARTS[key],key+' independent service module')
 used={'CoreTub','CoreLid','ElectronicsCassette'}
 def occ(key,t,label,parent=None):
  if key not in used:
   o=PARTS[key];used.add(key);o.transform2=t
   if DESIGN.snapshots.hasPendingSnapshot:DESIGN.snapshots.add()
  else:o=ROOT.occurrences.addExistingComponent(PARTS[key].component,t)
  o.attributes.add('Hexapod','AssemblyLabel',label)
  if parent:rigid(parent,o,label+' fixed')
  return o
 legs=[]
 for n,a in enumerate(range(0,LEG_COUNT*60,60),1):
  yawpt=position(a,DEFAULT['yaw_radius'],0,0);shoulder,knee,foot=stance(a)
  tang=position(a,0,1,0)
  cp=occ('CoxaCarrier',matrix(a,0,yawpt),f'L{n} coxa')
  fp=occ('FemurCarrier',matrix(a,DEFAULT['femur_angle'],shoulder),f'L{n} femur')
  occ('FemurCheek',matrix(a,DEFAULT['femur_angle'],shoulder),f'L{n} femur cheek',fp)
  tb=occ('Tibia',matrix(a,DEFAULT['tibia_angle'],knee),f'L{n} tibia')
  occ('FootPad',matrix(a,DEFAULT['tibia_angle'],knee),f'L{n} foot pad',tb)
  occ('YawReserve',matrix(a,0,yawpt),f'L{n} yaw actuator reserve',chassis)
  occ('HipReserve',matrix(a,DEFAULT['femur_angle'],shoulder),f'L{n} hip actuator reserve inverted case',fp)
  occ('KneeReserve',matrix(a,DEFAULT['femur_angle'],shoulder),f'L{n} knee actuator reserve',fp)
  js=[revolute(chassis,cp,yawpt,(0,0,1),f'L{n} · YAW architecture',(-20,20)),revolute(cp,fp,shoulder,tang,f'L{n} · HIP architecture',(-12,12)),revolute(fp,tb,knee,tang,f'L{n} · KNEE architecture',(-15,15))]
  legs.append({'n':n,'joints':js,'foot':geometry.foot(a,0,0,0)})
  log('Assembled enclosed leg '+str(n))
 return legs

def service_screw(label,axis,x,y,shaft_start,length,head_start,head_end,parent,t=None):
 o=component('SERVICE HARDWARE | '+label);c=o.component
 extrude(c,axis,shaft_start,[circ(x,y,1.5)],length,F.NewBodyFeatureOperation,'M3 shaft envelope; threads not modeled')
 add(c,axis,head_start,[circ(x,y,2.8)],head_end-head_start,'Recessed socket head')
 color(c,(42,45,48))
 if t:o.transform2=t
 if DESIGN.snapshots.hasPendingSnapshot:DESIGN.snapshots.add()
 rigid(parent,o,label+' attached for concept visualization')
 c.attributes.add('Hexapod','PurchasedHardware','Provisional M3 service fastener; actual insert and thread engagement TBD')
 return o

def hardware():
 import v3_core_layout as core_layout
 for index,(x,y) in enumerate(core_layout.lid_fasteners(),1):
  service_screw('Core lid '+str(index),'z',x,y,-30,30,-31.8,-30,PARTS['CoreTub'])
 for index,(x,y) in enumerate(core_layout.cassette_fasteners(),1):
  service_screw('Cassette '+str(index),'z',x,y,-19,6,-13,-11.2,PARTS['ElectronicsCassette'])
 labels={o.attributes.itemByName('Hexapod','AssemblyLabel').value:o for o in ROOT.occurrences if o.attributes.itemByName('Hexapod','AssemblyLabel')}
 for n in range(1,LEG_COUNT+1):
  fp=labels[f'L{n} femur']
  service_screw(f'L{n} upper cover','y',26,8.1,-16.9,30,-18.7,-16.9,fp,fp.transform2)
  FASTENERS.append({'label':f'L{n} front cover','axis':'y','x_mm':26,'z_mm':8.1,'shaft_start_axis_mm':-16.9,'shaft_end_axis_mm':13.1,'quantity':1,'diameter_mm':3,'nominal_length_mm':30,'visible_from_front':False,'status':'provisional service fastener; all actuator horn and passive pivot hardware additional'})

def interference():
 entities=adsk.core.ObjectCollection.create()
 for o in ROOT.occurrences:entities.add(o)
 inp=DESIGN.createInterferenceInput(entities);inp.areCoincidentFacesIncluded=False
 results=DESIGN.analyzeInterference(inp);out=[]
 for r in results:
  if r.interferenceBody.volume>1e-7:
   out.append({'a':r.entityOne.parentComponent.name,'b':r.entityTwo.parentComponent.name,'a_occ':r.entityOne.assemblyContext.name if r.entityOne.assemblyContext else None,'b_occ':r.entityTwo.assemblyContext.name if r.entityTwo.assemblyContext else None,'volume_cm3':r.interferenceBody.volume})
 return out

def report(legs):
 rows=[]
 for key,c,qty,axis,bed in PRINTS:
  b=c.bRepBodies.item(0)
  assert c.bRepBodies.count==1 and b.isSolid and b.volume>0,key
  rows.append({'part':key,'quantity':qty,'volume_cm3':b.volume,'solid_PLA_mass_g':b.volume*1.24*qty,'print_bed_normal':axis,'bed_mm':bed})
 issues=[]
 for i in range(DESIGN.timeline.count):
  item=DESIGN.timeline.item(i)
  if item.healthState!=adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState:issues.append({'index':i,'name':item.name,'state':str(item.healthState)})
 data={'status':'FORM AND ARCHITECTURE CONCEPT; actuator not selected; not ready to manufacture','reference':'ManufacturedMotion/Hex visual and architecture study; original geometry, no copied CAD meshes','build_revision':BUILD_REVISION,'leg_count':LEG_COUNT,'alignment':'hip knee and toe centre lines share local Y0 plane','hip_actuator_layout':'case on femur, output fixed to proximal clevis; inverted mounting','occurrences':ROOT.occurrences.count,'revolute_joints':sum(j.jointMotion.jointType==adsk.fusion.JointTypes.RevoluteJointType for j in JOINTS),'rigid_joints':sum(j.jointMotion.jointType==adsk.fusion.JointTypes.RigidJointType for j in JOINTS),'hard_print_quantity':sum(r['quantity'] for r in rows if r['part']!='FootPad'),'compliant_print_quantity':LEG_COUNT,'print_parts':rows,'solid_PLA_mass_g_excluding_TPU':sum(r['solid_PLA_mass_g'] for r in rows if r['part']!='FootPad'),'modeled_service_screw_quantity':len(FASTENERS),'actuator_mount_horn_pivot_hardware':'TBD; excluded from modeled service screw count','timeline_issues':issues,'neutral_interferences':interference(),'foot_reference_kind':'toe boot centre at local (93,0,0); not ground contact', 'foot_reference_points_mm':[l['foot'] for l in legs]}
 open(OUT+'/CAD-validation.json','w').write(json.dumps(data,indent=2))
 open(OUT+'/Service-fasteners.json','w').write(json.dumps(FASTENERS,indent=2))
 assert data['revolute_joints']==3*LEG_COUNT
 assert not issues,'Unhealthy features'
 assert not data['neutral_interferences'],'Neutral intersections'
 assert len(FASTENERS)==6+LEG_COUNT,'Service screw count mismatch'
 assert len(set(f['label'] for f in FASTENERS))==6+LEG_COUNT,'Duplicate fastener path labels'
 log('Neutral interference count '+str(len(data['neutral_interferences'])))
 return data

def exports():
 m=DESIGN.exportManager;folder=OUT+'/STL-CONCEPT';os.makedirs(folder,exist_ok=True)
 for key,c,qty,axis,bed in PRINTS:
  opt=m.createSTLExportOptions(c.bRepBodies.item(0),folder+'/'+key+'.stl');opt.meshRefinement=adsk.fusion.MeshRefinementSettings.MeshRefinementHigh;opt.unitType=adsk.fusion.DistanceUnits.MillimeterDistanceUnits;opt.sendToPrintUtility=False
  assert m.execute(opt);log('Exported '+key)
 assert m.execute(m.createFusionArchiveExportOptions(OUT+'/HX18-Inline-V5-Concept.f3d'))
 assert m.execute(m.createSTEPExportOptions(OUT+'/HX18-Inline-V5-Concept.step'))
 camera=adsk.core.Application.get().activeViewport.camera
 camera.viewOrientation=adsk.core.ViewOrientations.ArbitraryViewOrientation
 camera.eye=pt(300,-330,230);camera.target=pt(0,0,-10);camera.upVector=V(0,0,1);camera.isSmoothTransition=False;camera.isFitView=True
 DESIGN.parentDocument.activate();DESIGN.activateRootComponent();vp=adsk.core.Application.get().activeViewport
 vp.visualStyle=adsk.core.VisualStyles.ShadedVisualStyle;vp.camera=camera
 vp.saveAsImageFile(OUT+'/HX18-Inline-V5-preview.png',1800,1400)


def run(context):
 global ROOT,DESIGN,PARTS,PRINTS,JOINTS,FASTENERS,LEG_COUNT,BUILD_REVISION,OUT
 try:
  app=adsk.core.Application.get()
  LEG_COUNT=int(context.get('leg_count',6)) if isinstance(context,dict) else 6
  assert LEG_COUNT in (1,6)
  BUILD_REVISION='V5-inline-'+str(LEG_COUNT)
  OUT=os.path.join(BASE_ROOT,'prototype' if LEG_COUNT==1 else 'generated');os.makedirs(OUT,exist_ok=True)
  if os.path.exists(os.path.join(OUT,'Error.txt')):os.remove(os.path.join(OUT,'Error.txt'))
  if isinstance(context,dict) and context.get('audit_existing'):
   import v3_setup;importlib.reload(v3_setup);v3_setup.setup(sys.modules[__name__])
   for key in ('hx_servo_width','hx_servo_length','hx_servo_height'):
    param=DESIGN.userParameters.itemByName(key)
    if param:param.deleteMe()
   exports()
   import v3_setup;importlib.reload(v3_setup)
   import v3_audit,v3_verify;importlib.reload(v3_audit);importlib.reload(v3_verify)
   v3_audit.audit(sys.modules[__name__]);v3_verify.verify(sys.modules[__name__]);return
  PARTS={};PRINTS=[];JOINTS=[];FASTENERS=[]
  open(os.path.join(OUT,'Progress.log'),'w').write('Start\n')
  if os.path.exists(os.path.join(OUT,'Error.txt')):os.remove(os.path.join(OUT,'Error.txt'))
  doc=app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType);doc.activate()
  DESIGN=adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'));ROOT=DESIGN.rootComponent
  ROOT.attributes.add('Hexapod','BuildRevision',BUILD_REVISION)
  DESIGN.designIntent=adsk.fusion.DesignIntentTypes.HybridDesignIntentType
  doc.name='HX18 · INLINE V5 · compact enclosed concept'
  for k,v in DEFAULT.items():
   unit='deg' if 'angle' in k else 'mm'
   DESIGN.userParameters.add('hx_'+k,adsk.core.ValueInput.createByString(str(v)+' '+unit),unit,'Generator reference; exact actuator interfaces intentionally pending')
  import v3_core_layout;importlib.reload(v3_core_layout)
  import core_enclosure,leg_shells;importlib.reload(core_enclosure);importlib.reload(leg_shells)
  core_enclosure.build_parts(sys.modules[__name__]);leg_shells.build(sys.modules[__name__]);legs=assemble();core_enclosure.assemble_reserves(sys.modules[__name__]);hardware();data=report(legs);exports()
  log('NATIVE INLINE FORM EXPORT COMPLETE')
  import v3_setup;importlib.reload(v3_setup)
  import v3_audit,v3_verify;importlib.reload(v3_audit);importlib.reload(v3_verify)
  v3_audit.audit(sys.modules[__name__]);v3_verify.verify(sys.modules[__name__])
  log('BUILD EXPORT MOTION AND ARCHIVE CHECKS COMPLETE')
 except:
  open(os.path.join(OUT,'Error.txt'),'w').write(traceback.format_exc());log('FAILED '+traceback.format_exc())
