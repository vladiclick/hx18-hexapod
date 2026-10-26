import adsk.core,adsk.fusion,json

def setup(b):
 app=adsk.core.Application.get()
 def matches(design):
  attr=design.rootComponent.attributes.itemByName('Hexapod','BuildRevision') if design else None
  return bool(attr and attr.value==b.BUILD_REVISION)
 target=b.DESIGN if matches(b.DESIGN) else None
 if target is None:
  active=app.activeDocument
  design=adsk.fusion.Design.cast(active.products.itemByProductType('DesignProductType')) if active else None
  if matches(design):target=design
 if target is None:
  candidates=[]
  for doc in app.documents:
   design=adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
   if matches(design):candidates.append(design)
  assert len(candidates)==1,'Select the intended V5 document before re-running its audit'
  target=candidates[0]
 assert target,'Current inline concept is not open'
 b.DESIGN=target;b.DESIGN.parentDocument.activate();b.ROOT=target.rootComponent
 b.PARTS={};b.PRINTS=[];seen=set()
 for o in b.ROOT.occurrences:
  c=o.component;a=c.attributes.itemByName('Hexapod','Print')
  if a and c.entityToken not in seen:
   seen.add(c.entityToken);p=json.loads(a.value);key=c.bRepBodies.item(0).name
   b.PARTS[key]=o;b.PRINTS.append((key,c,p['quantity'],p['bed_normal'],p['bed_offset_mm']))
 b.JOINTS=list(b.ROOT.asBuiltJoints)
 b.FASTENERS=json.load(open(b.OUT+'/Service-fasteners.json'))
 assert 'CoreTub' in b.PARTS and len(b.PRINTS)==8
 return app
