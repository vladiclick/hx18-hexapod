import adsk.core,adsk.fusion,json,math
from core_layout import *
def repair(b):
 app=adsk.core.Application.get();b.DESIGN=adsk.fusion.Design.cast(app.activeProduct);b.ROOT=b.DESIGN.rootComponent;b.PRINTS=[];b.PARTS={};b.JOINTS=list(b.ROOT.asBuiltJoints)
 seen=set()
 for o in b.ROOT.occurrences:
  c=o.component
  if c.entityToken in seen:continue
  seen.add(c.entityToken)
  a=c.attributes.itemByName('Hexapod','Print')
  if a:
   key=c.bRepBodies.item(0).name;b.PARTS[key]=o;p=json.loads(a.value)
   b.PRINTS.append((key,c,p['quantity'],p['bed_normal'],p['bed_offset_mm']))
 buckholes=[(x-15.875,y-21.59) for x,y in [(2.159,2.159),(27.559,2.159),(2.159,41.021),(27.559,41.021)]]
 b.cut(b.PARTS['Chassis'].component,'z',-9,[b.circ(x,y,2.1) for x,y in buckholes],3,'Regulator M2 socket head insertion access')
 pc=b.PARTS['PowerShelf'].component
 for a in range(0,360,60):
  points=[b.position(a,49+x,y,0)[:2] for x,y in [(-21.5,-6.7),(12.3,-6.7),(12.3,6.7),(-21.5,6.7)]]
  # Some clipping polygons do not intersect at all; only corner pair orientations needcuts.
  if a in [60,120,240,300]:b.cut(pc,'z',-6,[b.poly(points)],3,'Yaw servo ear service clearance')
 for o in b.ROOT.occurrences:
  c=o.component
  if 'Servo buck M2x8' in c.name:
   for x,y in buckholes:b.add(c,'z',2,[b.circ(x,y,1)],2,'M2x10 complete nut engagement')
   c.name=c.name.replace('M2x8','M2x10');c.attributes.add('Hexapod','PurchasedHardware','Servo buck M2x10')
   break
 for key in ['PowerShelf','Chassis']:
  c=b.PARTS[key].component;c.attributes.add('Hexapod','RegisteredVolume',str(c.bRepBodies.item(0).volume))
 legs=[{'foot':b.stance(a)[2]} for a in range(0,360,60)]
 b.verify(legs);b.export_all();b.log('REPAIR COMPLETE')
