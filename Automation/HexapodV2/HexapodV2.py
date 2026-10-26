import adsk.core, adsk.fusion, math, traceback, json, os, sys, time
OUT=os.path.abspath(os.path.join(os.path.dirname(__file__),'../..'))
BASE=OUT
os.makedirs(OUT+'/Automation/logs',exist_ok=True)
sys.path.insert(0,os.path.dirname(__file__))
import geometry, importlib
import center_core
importlib.reload(geometry)
from geometry import DEFAULT, transform, position, stance, capsule
P=adsk.core.Point3D.create
V=adsk.core.Vector3D.create
VI=adsk.core.ValueInput.createByReal
F=adsk.fusion.FeatureOperations
ROOT=None
DESIGN=None
PARTS={}
PRINTS=[]
JOINTS=[]
def log(s):
 with open(OUT+'/Automation/logs/v2-progress.txt','a') as f:f.write(s+'\n')
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
 plane=c.xYConstructionPlane if axis=='z' else c.xZConstructionPlane
 normal=plane.geometry.normal.z if axis=='z' else plane.geometry.normal.y
 if offset:
  i=c.constructionPlanes.createInput();i.setByOffset(plane,VI(offset/10/normal))
  plane=c.constructionPlanes.add(i);plane.name=name+' plane';plane.isLightBulbOn=False
 s=c.sketches.add(plane);s.name=name
 return s

def mappt(s,axis,offset,a):
 return s.modelToSketchSpace(pt(a[0],a[1],offset) if axis=='z' else pt(a[0],offset,a[1]))

def profile(c,axis,offset,loops,name):
 s=sketch(c,axis,offset,name);s.isComputeDeferred=True
 for kind,data in loops:
  if kind=='circle':
   x,y,r=data;s.sketchCurves.sketchCircles.addByCenterRadius(mappt(s,axis,offset,(x,y)),r/10)
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
 normal=s.referencePlane.geometry.normal.z if axis=='z' else s.referencePlane.geometry.normal.y
 i.setDistanceExtent(False,VI(depth/10/normal))
 if op==F.CutFeatureOperation:i.participantBodies=[b for b in c.bRepBodies]
 e=c.features.extrudeFeatures.add(i);e.name=name;s.isLightBulbOn=False
 return e

def rect(x0,y0,x1,y1):return ('poly',[(x0,y0),(x1,y0),(x1,y1),(x0,y1)])
def circ(x,y,r):return ('circle',(x,y,r))
def cap(a,b,r):return ('poly',capsule(a,b,r))
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

def horn_holes(c,axis,off,d,center=(0,0)):
 x,z=center
 cut(c,axis,off,[circ(x,z,2.6),cap((x+6.8,z),(x+10.7,z),1.2),cap((x-10.7,z),(x-6.8,z),1.2)],d,'Stock horn screw access and adjustable M2 slots')

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
 PARTS[key]=o;PRINTS.append((key,c,qty,axis,bed));color(c,(35,132,128) if key in ['CoxaPlate','FemurPlate','Tibia'] else (47,54,63))
 log('Built '+key)

def build_parts():
 o=component('01 | Chassis · ground');c=o.component
 outer=[(69*math.cos(i*math.pi/3),69*math.sin(i*math.pi/3)) for i in range(6)]
 add(c,'z',-9,[poly(outer)],3,'Hexagonal chassis')
 cut(c,'z',-9,[poly([(22*math.cos(i*math.pi/3),22*math.sin(i*math.pi/3)) for i in range(6)])],3,'Central wiring aperture')
 for a in range(0,360,60):
  def rloop(points):return poly([position(a,49+x,y,0)[:2] for x,y in points])
  cut(c,'z',-9,[rloop([(-16.3,-6.5),(7.1,-6.5),(7.1,6.5),(-16.3,6.5)])],3,'Yaw MG90S body clearance')
  cut(c,'z',-9,[rloop(capsule((-19.6,0),(-17.4,0),1.2)),rloop(capsule((8.2,0),(10.4,0),1.2))],3,'Yaw ear fastener adjustment')
  x,y,_=position(a+30,32,0,0);cut(c,'z',-9,[circ(x,y,1.7)],3,'M3 deck mounting')
 for a in range(30,360,60):
  points=[position(a,x,y,0)[:2] for x,y in [(38,-5),(52,-5),(56,0),(52,5),(38,5),(38,0)]]
  cut(c,'z',-9,[poly(points)],3,'Lightening and cable window')
 register(o,'Chassis',1,bed=-9)
 import center_core;importlib.reload(center_core);center_core.build_prints(sys.modules[__name__])
 o=component('03 | Coxa yaw plate');c=o.component
 add(c,'z',4,[circ(0,0,13.5)],3,'Rounded coxa hub')
 add(c,'z',4,[poly([(0,-13.5),(15,-12),(46,-8.5),(46,8.5),(15,12),(0,13.5)])],3,'Tapered coxa carrier')
 horn_holes(c,'z',4,3)
 cut(c,'z',4,[circ(17,4,1.7),circ(42,4,1.7),cap((16,-6),(35,-6),2.5)],3,'Hip bracket bolts and lightening')
 register(o,'CoxaPlate',6,bed=4)
 o=component('04 | Hip removable servo bracket');c=o.component
 add(c,'z',7,[rect(8,-11,46,8)],3,'Flat mounting foot')
 add(c,'y',-9,[rect(8,10,46,50)],3,'Upright servo mounting frame')
 cut(c,'y',-9,[rect(13.7,31.5,37.1,51)],3,'MG90S shoulder clearance')
 cut(c,'y',-9,[cap((10.4,38),(12.6,38),1.2),cap((38.2,38),(40.4,38),1.2)],3,'Shoulder ear mounting slots')
 cut(c,'z',7,[circ(17,4,1.7),circ(42,4,1.7)],3,'M3 mounting foot holes')
 cut(c,'y',-9,[poly([(19,12),(32,12),(32,19.5),(25.5,26),(19,19.5)])],3,'Self-supporting lightening window')
 cut(c,'z',7,[circ(8.5,0,3)],3,'Yaw horn nut and tool access')
 for x in [17,42]:cone_loft(c,'z',x,4,[(8.5,1.7),(10,3.2)],F.CutFeatureOperation,'M3 90 degree countersink')
 register(o,'HipBracket',6,bed=7)
 o=component('05 | Femur horn link');c=o.component
 add(c,'y',4,[cap((0,0),(22.5,0),13.5)],3,'Femur plate')
 horn_holes(c,'y',4,3)
 cut(c,'y',4,[circ(22.5,-10,1.2),circ(22.5,10,1.2),cap((15,-2),(25,-2),2)],3,'Knee mount fastening and lightening')
 # Remove the unnecessary far end; clearance to moving tibia horn head.
 cut(c,'y',4,[rect(26.5,-20,40,20)],3,'Tibia swing clearance')
 register(o,'FemurPlate',6,'y',4)
 o=component('06 | Knee servo mount');c=o.component
 add(c,'y',25,[rect(19,-13.5,56,13.5)],3,'Knee frame')
 cut(c,'y',25,[rect(25.7,-6.5,49.1,6.5)],3,'MG90S knee body clearance')
 cut(c,'y',25,[cap((22.4,0),(24.6,0),1.2),cap((50.2,0),(52.4,0),1.2)],3,'Knee ear mounting adjustment')
 for z in [-10,10]:
  add(c,'y',7,[circ(22.5,z,3)],18,'Printed alignment tower')
  cut(c,'y',7,[circ(22.5,z,1.2)],21,'M2 femur through fastener')
 register(o,'KneeMount',6,'-y',28)
 o=component('07 | Tibia · tapered foot');c=o.component
 add(c,'y',12,[circ(0,0,13.5)],3,'Horn hub')
 add(c,'y',12,[poly([(4,-8),(72,-4),(80,-2.5),(80,2.5),(72,4),(4,8)])],3,'Tapered tibia blade')
 add(c,'y',12,[circ(78,0,4.5)],3,'Rounded foot contact')
 horn_holes(c,'y',12,3)
 cut(c,'y',12,[cap((19,0),(62,0),2.3),circ(75,0,1.7)],3,'Lightening and optional rubber pad screw')
 register(o,'Tibia',6,'y',12)
 o=component('MG90S | case envelope · measure actual ears');c=o.component
 add(c,'z',-25,[rect(-16,-6.2,6.8,6.2)],23.5,'MG90S case nominal envelope')
 add(c,'z',-6,[rect(-21,-6.2,11.8,6.2)],3,'Mounting ears approximate')
 cut(c,'z',-6,[circ(-18.5,0,1),circ(9.3,0,1)],3,'Nominal ear holes')
 add(c,'z',-1.5,[circ(0,0,5.5)],2,'Gearbox boss envelope')
 add(c,'z',0.5,[circ(0,0,2.3)],1.5,'Output shaft envelope')
 PARTS['Servo']=o;color(c,(66,77,88));log('Built servo envelope')
 o=component('Stock double horn | reference only');c=o.component
 add(c,'z',2,[cap((-10.5,0),(10.5,0),2.5)],2,'Supplied horn approximate')
 add(c,'z',0.5,[circ(0,0,5.5)],3.5,'Horn hub')
 cut(c,'z',0.5,[circ(0,0,2.35),circ(-8.5,0,0.8),circ(8.5,0,0.8)],3.5,'Stock horn screw references')
 PARTS['Horn']=o;color(c,(224,221,209));log('Built stock horn envelope')
 # Quick print test retains both interface types.
 o=component('FIT TEST ONLY · servo and horn coupon');c=o.component
 add(c,'z',0,[rect(-24,-11,15,11)],3,'Servo fit coupon')
 cut(c,'z',0,[rect(-16.3,-6.5,7.1,6.5),cap((-19.6,0),(-17.4,0),1.2),cap((8.2,0),(10.4,0),1.2)],3,'Servo test opening and slots')
 add(c,'z',0,[cap((26,0),(32,0),13.5)],3,'Connected horn test hub')
 horn_holes(c,'z',0,3,(30,0));register(o,'FitCoupon',1,bed=0);o.isLightBulbOn=False

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
 chassis=PARTS['Chassis'];chassis.isGrounded=True
 for key in ['LowerDeck','ElectronicsDeck','PowerShelf','CoreBridge','CoreCap']:rigid(chassis,PARTS[key],key+' rigid to chassis')
 used=set(['Chassis','LowerDeck','ElectronicsDeck','PowerShelf','CoreBridge','CoreCap','FitCoupon'])
 def occ(key,t,name):
  if key not in used:
   o=PARTS[key];used.add(key);o.transform2=t
   if DESIGN.snapshots.hasPendingSnapshot:DESIGN.snapshots.add()
  else:o=ROOT.occurrences.addExistingComponent(PARTS[key].component,t)
  o.attributes.add('Hexapod','AssemblyLabel',name)
  return o
 legs=[]
 for n,a in enumerate(range(0,360,60),1):
  yawpt=position(a,49,0,0);shoulder,knee,foot=stance(a)
  tang=position(a,0,1,0)
  lower=occ('LowerSpacer',matrix(0,0,position(a+30,32,0,0)),f'L{n} lower spacer')
  upper=occ('UpperSpacer',matrix(0,0,position(a+30,32,0,0)),f'L{n} upper spacer')
  rigid(chassis,lower,f'L{n} lower spacer rigid');rigid(chassis,upper,f'L{n} upper spacer rigid')
  ys=occ('Servo',matrix(a,0,yawpt),f'L{n} yaw servo');rigid(chassis,ys,f'L{n} yaw case rigid')
  cp=occ('CoxaPlate',matrix(a,0,yawpt),f'L{n} coxa')
  hm=occ('HipBracket',matrix(a,0,yawpt),f'L{n} hip mount');rigid(cp,hm,f'L{n} hip mount rigid')
  yh=occ('Horn',matrix(a,0,yawpt),f'L{n} yaw horn');rigid(cp,yh,f'L{n} yaw horn rigid')
  hs=occ('Servo',matrix(a,0,shoulder,True),f'L{n} shoulder servo');rigid(cp,hs,f'L{n} shoulder case rigid')
  fp=occ('FemurPlate',matrix(a,-25,shoulder),f'L{n} femur')
  km=occ('KneeMount',matrix(a,-25,shoulder),f'L{n} knee mount');rigid(fp,km,f'L{n} knee mount rigid')
  sh=occ('Horn',matrix(a,-25,shoulder,True),f'L{n} shoulder horn');rigid(fp,sh,f'L{n} shoulder horn rigid')
  knee_servo_point=tuple(knee[i]+19*tang[i] for i in range(3))
  ks=occ('Servo',matrix(a,-25,knee_servo_point,-1),f'L{n} knee servo');rigid(fp,ks,f'L{n} knee case rigid')
  tb=occ('Tibia',matrix(a,-95,knee),f'L{n} tibia')
  kh=occ('Horn',matrix(a,-95,knee_servo_point,-1),f'L{n} knee horn');rigid(tb,kh,f'L{n} knee horn rigid')
  js=[revolute(chassis,cp,yawpt,(0,0,1),f'L{n} · 01 COXA YAW',(-25,25)),revolute(cp,fp,shoulder,tang,f'L{n} · 02 FEMUR PITCH',(-15,15)),revolute(fp,tb,knee,tang,f'L{n} · 03 KNEE PITCH',(-15,15))]
  legs.append({'n':n,'joints':js,'shoulder':shoulder,'knee':knee,'foot':foot})
  log(f'Assembled leg {n} with 3 revolute joints')
 return legs

def cut_hardware_body(c,axis,offset,loop,depth,body,name):
 s=profile(c,axis,offset,[loop],name)
 i=c.features.extrudeFeatures.createInput(s.profiles.item(0),F.CutFeatureOperation)
 normal=s.referencePlane.geometry.normal.z if axis=='z' else s.referencePlane.geometry.normal.y
 i.setDistanceExtent(False,VI(depth/10/normal));i.participantBodies=[body]
 e=c.features.extrudeFeatures.add(i);e.name=name;s.isLightBulbOn=False

def hardware_template(name,axis,holes,start,length,seat,diam,af):
 o=component('HARDWARE | '+name+' · unthreaded reference');c=o.component
 head_height=3 if diam==3 else (2 if diam==2 else 1.6)
 nut_height=2.4 if diam==3 else (1.6 if diam==2 else 1.3)
 head_radius=2.8 if diam==3 else (1.9 if diam==2 else 1.5)
 for n,(x,y) in enumerate(holes,1):
  bolt=extrude(c,axis,start,[circ(x,y,diam/2)],length,F.NewBodyFeatureOperation,'Bolt shank')
  add(c,axis,start-head_height,[circ(x,y,head_radius)],head_height,'Socket head envelope')
  bolt.bodies.item(0).name=name+' bolt '+str(n)
  washer=extrude(c,axis,seat,[circ(x,y,af/2)],0.4,F.NewBodyFeatureOperation,'Washer')
  wb=washer.bodies.item(0);cut_hardware_body(c,axis,seat,circ(x,y,(diam+0.4)/2),0.4,wb,'Washer clearance')
  r=af/math.sqrt(3)
  points=[(x+r*math.cos(k*math.pi/3),y+r*math.sin(k*math.pi/3)) for k in range(6)]
  nut=extrude(c,axis,seat+0.4,[poly(points)],nut_height,F.NewBodyFeatureOperation,'Hex nut')
  nb=nut.bodies.item(0);nb.name=name+' nut '+str(n)
  cut_hardware_body(c,axis,seat+0.4,circ(x,y,(diam+0.3)/2),nut_height,nb,'Nut thread envelope clearance')
 assert c.bRepBodies.count==len(holes)*3,name+' hardware bodies merged unexpectedly'
 c.attributes.add('Hexapod','PurchasedHardware',name);color(c,(170,182,189));return o

def countersunk_hip_hardware():
 o=component('HARDWARE | M3x10 countersunk hip · reference');c=o.component
 for x in [17,42]:
  extrude(c,'z',0,[circ(x,4,1.5)],8.5,F.NewBodyFeatureOperation,'Countersunk M3 shank')
  cone_loft(c,'z',x,4,[(8.5,1.5),(10,3)],F.JoinFeatureOperation,'Flush 90 degree screw head')
  washer=extrude(c,'z',3.6,[circ(x,4,2.75)],0.4,F.NewBodyFeatureOperation,'M3 underside washer')
  cut_hardware_body(c,'z',3.6,circ(x,4,1.7),0.4,washer.bodies.item(0),'Washer clearance')
  r=5.5/math.sqrt(3)
  nut=extrude(c,'z',1.2,[poly([(x+r*math.cos(k*math.pi/3),4+r*math.sin(k*math.pi/3)) for k in range(6)])],2.4,F.NewBodyFeatureOperation,'M3 underside nut')
  cut_hardware_body(c,'z',1.2,circ(x,4,1.65),2.4,nut.bodies.item(0),'Nut thread envelope clearance')
 assert c.bRepBodies.count==6
 c.attributes.add('Hexapod','PurchasedHardware','M3x10 countersunk hip');color(c,(170,182,189));return o

def reverse_stack_hardware():
 o=hardware_template('M3x50 chassis stack','z',[(x,-y) for x,y in __import__('core_layout').stack_points()],0,50,44,3,5.5)
 # Native0 bolt seat atglobal15; axis pointsDOWN, washer atglobal-29.
 # matrix servo=-1 maps nativeZ to-Y, so use explicit reverseZ basis instead.
 m=adsk.core.Matrix3D.create();m.setWithCoordinateSystem(pt(0,0,15),V(1,0,0),V(0,-1,0),V(0,0,-1));o.transform2=m
 if DESIGN.snapshots.hasPendingSnapshot:DESIGN.snapshots.add()
 # Use pretransformed geometry? Caller passes identity; invertnativecomponent geometry through placement below.
 o.attributes.add('Hexapod','StackReverse','true');return o

def build_hardware():
 templates={
  'M2x8 servo ears':hardware_template('M2x8 servo ears','z',[(-18.5,0),(9.3,0)],-9,8,-3,2,4),
  'M1_6x8 stock horn':hardware_template('M1_6x8 stock horn','z',[(-8.5,0),(8.5,0)],2,8,7,1.6,3.2),
  'M3x10 countersunk hip':countersunk_hip_hardware(),
  'M2x30 knee towers':hardware_template('M2x30 knee towers','y',[(22.5,-10),(22.5,10)],4,30,28,2,4),
  'M3x50 chassis stack':reverse_stack_hardware()}
 used=set()
 labels={o.attributes.itemByName('Hexapod','AssemblyLabel').value:o for o in ROOT.occurrences if o.attributes.itemByName('Hexapod','AssemblyLabel')}
 def place(key,anchor,t,label):
  if key in used:o=ROOT.occurrences.addExistingComponent(templates[key].component,t)
  else:
   o=templates[key];o.transform2=t;used.add(key)
   if DESIGN.snapshots.hasPendingSnapshot:DESIGN.snapshots.add()
  o.attributes.add('Hexapod','AssemblyLabel',label);rigid(anchor,o,label+' rigid')
 for n in range(1,7):
  for kind in ['yaw','shoulder','knee']:
   case=labels[f'L{n} {kind} servo'];horn=labels[f'L{n} {kind} horn']
   place('M2x8 servo ears',case,case.transform2,f'L{n} {kind} mounting screws')
   place('M1_6x8 stock horn',horn,horn.transform2,f'L{n} {kind} horn fastening')
  cp=labels[f'L{n} coxa'];fp=labels[f'L{n} femur']
  place('M3x10 countersunk hip',cp,cp.transform2,f'L{n} hip bracket bolts')
  place('M2x30 knee towers',fp,fp.transform2,f'L{n} knee tower bolts')
 place('M3x50 chassis stack',PARTS['Chassis'],templates['M3x50 chassis stack'].transform2,'Chassis stack through bolts')
 log('Purchased fastener envelopes assembled')

def verify(legs):
 report={'status':'CAD prototype; physical fit not validated','original_sketch_preserved':True,'occurrences':ROOT.occurrences.count,'revolute_joints':0,'rigid_joints':0,'print_parts':[],'foot_centres_mm':[l['foot'] for l in legs],'timeline_issues':[]}
 for j in JOINTS:
  if j.jointMotion.jointType==adsk.fusion.JointTypes.RevoluteJointType:report['revolute_joints']+=1
  elif j.jointMotion.jointType==adsk.fusion.JointTypes.RigidJointType:report['rigid_joints']+=1
 assert report['revolute_joints']==18
 for key,c,qty,axis,bed in PRINTS:
  b=c.bRepBodies.item(0);assert b.isSolid and b.volume>0
  assert abs(b.volume-float(c.attributes.itemByName('Hexapod','RegisteredVolume').value))<1e-7,key+' changed during assembly'
  report['print_parts'].append({'part':key,'quantity':qty,'volume_cm3':b.volume,'PLA_mass_g_at_1_24':b.volume*1.24*qty,'print_bed_normal':axis,'bed_mm':bed})
 for i in range(DESIGN.timeline.count):
  item=DESIGN.timeline.item(i)
  if item.healthState!=adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState:report['timeline_issues'].append({'index':i,'name':item.name,'state':item.healthState})
 entities=adsk.core.ObjectCollection.create()
 for o in ROOT.occurrences:
  if o.component.name.startswith('FIT TEST'):continue
  entities.add(o)
 inp=DESIGN.createInterferenceInput(entities);inp.areCoincidentFacesIncluded=False
 try:
  result=DESIGN.analyzeInterference(inp)
  report['neutral_interferences']=[]
  for r in result:
   report['neutral_interferences'].append({'a':r.entityOne.parentComponent.name,'b':r.entityTwo.parentComponent.name,'volume_cm3':r.interferenceBody.volume,'a_occ':r.entityOne.assemblyContext.name if r.entityOne.assemblyContext else None,'b_occ':r.entityTwo.assemblyContext.name if r.entityTwo.assemblyContext else None})
 except:report['interference_error']=traceback.format_exc()
 report['printed_solid_volume_mass_g']=sum(p['PLA_mass_g_at_1_24'] for p in report['print_parts'] if p['part']!='FitCoupon')
 open(OUT+'/CAD-validation.json','w').write(json.dumps(report,indent=2))
 log('Validation report written')
 assert not report['timeline_issues'],'Unhealthy CAD timeline'
 assert not report.get('interference_error'),'Interference analysis failed'
 assert not report['neutral_interferences'],'Neutral pose collision'
 return report

def export_all():
 manager=DESIGN.exportManager;folder=OUT+'/STL';os.makedirs(folder,exist_ok=True)
 for key,c,qty,axis,bed in PRINTS:
  opt=manager.createSTLExportOptions(c.bRepBodies.item(0),folder+'/'+key+'.stl')
  opt.meshRefinement=adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
  opt.unitType=adsk.fusion.DistanceUnits.MillimeterDistanceUnits
  opt.sendToPrintUtility=False;assert manager.execute(opt)
  log('Exported '+key+' STL')
 assert manager.execute(manager.createFusionArchiveExportOptions(OUT+'/HX18-MG90S.f3d'))
 assert manager.execute(manager.createSTEPExportOptions(OUT+'/HX18-MG90S.step'))
 log('Exported Fusion archive and STEP')

def run(context):
 global ROOT,DESIGN
 if os.path.exists(OUT+'/Automation/logs/v2-cap-mode'):
  try:
   import cap_strengthen;importlib.reload(cap_strengthen);cap_strengthen.strengthen(sys.modules[__name__])
  except:open(OUT+'/Automation/logs/v2-cap-error.txt','w').write(traceback.format_exc())
  return
 if os.path.exists(OUT+'/Automation/logs/v2-finish-mode'):
  try:
   import cad_finish;importlib.reload(cad_finish);cad_finish.finish()
  except:open(OUT+'/Automation/logs/v2-finish-error.txt','w').write(traceback.format_exc())
  return
 if os.path.exists(OUT+'/Automation/logs/v2-gait-mode'):
  try:
   import cad_gait_audit;importlib.reload(cad_gait_audit);cad_gait_audit.run_audit()
  except:open(OUT+'/Automation/logs/v2-gait-error.txt','w').write(traceback.format_exc())
  return
 if os.path.exists(OUT+'/Automation/logs/v2-repair-mode'):
  try:
   import repair_core;importlib.reload(repair_core);repair_core.repair(sys.modules[__name__])
  except:open(OUT+'/Automation/logs/v2-repair-error.txt','w').write(traceback.format_exc())
  return
 if False:
  try:
   import cad_finalize;importlib.reload(cad_finalize);cad_finalize.finalize()
  except:open(OUT+'/Automation/logs/finalize-error.txt','w').write(traceback.format_exc())
  return
 if os.path.exists(OUT+'/Automation/logs/v2-audit-mode'):
  try:
   sys.modules.pop('cad_audit',None);import cad_audit;cad_audit.run_audit()
  except:open(OUT+'/Automation/logs/v2-audit-error.txt','w').write(traceback.format_exc())
  return
 try:
  open(OUT+'/Automation/logs/v2-progress.txt','w').write('Start\n')
  if os.path.exists(OUT+'/Automation/logs/v2-error.txt'):os.remove(OUT+'/Automation/logs/v2-error.txt')
  app=adsk.core.Application.get()
  opts=app.importManager.createFusionArchiveImportOptions(OUT+'/Original-Sketch.f3d')
  doc=app.importManager.importToNewDocument(opts);DESIGN=adsk.fusion.Design.cast(app.activeProduct);ROOT=DESIGN.rootComponent
  doc.name='HX18-MG90S v2 · integrated ESP32 core'
  DESIGN.designIntent=adsk.fusion.DesignIntentTypes.HybridDesignIntentType
  for s in ROOT.sketches:s.name='REFERENCE | original leg sketch · oversized for MG90S';s.isLightBulbOn=False
  for k,v in DEFAULT.items():
   unit='deg' if 'angle' in k else 'mm'
   DESIGN.userParameters.add('hx_'+k,adsk.core.ValueInput.createByString(str(v)+' '+unit),unit,'Builder design reference; rebuild for dimension changes')
  build_parts();legs=assemble();build_hardware();center_core.assemble_core(sys.modules[__name__]);verify(legs);export_all()
  camera=app.activeViewport.camera;camera.viewOrientation=adsk.core.ViewOrientations.ArbitraryViewOrientation
  camera.eye=pt(280,-320,230);camera.target=pt(0,0,-10);camera.upVector=V(0,0,1);camera.isSmoothTransition=False;camera.isFitView=True;app.activeViewport.camera=camera
  app.activeViewport.saveAsImageFile(OUT+'/HX18-preview.png',1800,1400)
  log('COMPLETE')
 except:
  open(OUT+'/Automation/logs/v2-error.txt','w').write(traceback.format_exc());log('FAILED '+traceback.format_exc())
