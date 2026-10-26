import adsk.core,adsk.fusion,json,importlib,sys
from core_layout import guard_points
def strengthen(b):
 app=adsk.core.Application.get();b.DESIGN=adsk.fusion.Design.cast(app.activeProduct);b.ROOT=b.DESIGN.rootComponent;b.JOINTS=list(b.ROOT.asBuiltJoints);b.PRINTS=[];b.PARTS={};seen=set()
 for o in b.ROOT.occurrences:
  c=o.component
  if c.entityToken in seen:continue
  seen.add(c.entityToken);a=c.attributes.itemByName('Hexapod','Print')
  if a:
   key=c.bRepBodies.item(0).name;p=json.loads(a.value);b.PARTS[key]=o;b.PRINTS.append((key,c,p['quantity'],p['bed_normal'],p['bed_offset_mm']))
 c=b.PARTS['CoreCap'].component
 for x,y in guard_points():b.add(c,'z',55,[b.circ(x,y,4)],2.4,'Reinforced removable cap screw boss')
 b.cut(c,'z',55,[b.circ(x,y,1.2) for x,y in guard_points()],2.4,'M2 cap through holes')
 c.attributes.add('Hexapod','RegisteredVolume',str(c.bRepBodies.item(0).volume))
 b.verify([{'foot':b.stance(a)[2]} for a in range(0,360,60)]);b.export_all()
 sys.modules.pop('cad_audit',None);import cad_audit;cad_audit.run_audit()
 import cad_gait_audit;importlib.reload(cad_gait_audit);cad_gait_audit.run_audit()
 import cad_finish;importlib.reload(cad_finish);cad_finish.finish()
