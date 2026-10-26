"""Integrated printable electronics core. All dimensions mm; manufacturer PCB patterns."""
import math
from core_layout import *

def build_prints(b):
 def part(key):
  o=b.component('CORE | '+key);return o,o.component
 def finish(o,key,z,qty=1):b.register(o,key,qty,bed=z)
 stack=stack_points();guards=guard_points();holes=lambda pts,r:[b.circ(x,y,r) for x,y in pts]
 o,c=part('LowerDeck')
 b.add(c,'z',-29,[b.poly(ellipse(37,36))],3,'Battery tray base')
 b.cut(c,'z',-29,holes(stack,1.7)+[b.cap((-25,-17),(-25,17),1.5),b.cap((25,-17),(25,17),1.5)],3,'M3 stack and 3mm battery strap slots')
 # Retain pouch with low corner stops; soft foam/strap supplies retention, no rigid compression.
 for x in [-23.5,23.5]:
  for y in [-11,11]:b.add(c,'z',-26,[b.rect(x-1,y-2.5,x+1,y+2.5)],3,'Battery corner guide')
 finish(o,'LowerDeck',-29)
 o,c=part('PowerShelf')
 b.add(c,'z',-6,[b.rect(-18,-24,18,24)],3,'Ventilated regulator cradle')
 for x,y in stack:b.add(c,'z',-6,[b.cap((0,0),(x,y),3.5)],3,'Stack support spoke')
 # Center vent slots leave mount pads and wiring rails intact.
 b.cut(c,'z',-6,[b.cap((-7,y),(7,y),1.4) for y in [-15,-8,0,8,15]]+holes(stack,1.7),3,'Cooling and M3 stack through holes')
 buckholes=[(x-15.875,y-21.59) for x,y in [(2.159,2.159),(27.559,2.159),(2.159,41.021),(27.559,41.021)]]
 for x,y in buckholes:b.add(c,'z',-3,[b.circ(x,y,2.8)],2,'M2 regulator standoff')
 b.cut(c,'z',-6,holes(buckholes,1.2),5,'Pololu D42 exact M2 pattern')
 for a in [60,120,240,300]:
  pts=[b.position(a,49+x,y,0)[:2] for x,y in [(-21.5,-6.7),(12.3,-6.7),(12.3,6.7),(-21.5,6.7)]]
  b.cut(c,'z',-6,[b.poly(pts)],3,'Yaw servo ear service clearance')
 finish(o,'PowerShelf',-6)
 cc=b.PARTS['Chassis'].component
 b.cut(cc,'z',-9,holes(buckholes,2.1),3,'Regulator M2 socket head insertion access')
 cc.attributes.add('Hexapod','RegisteredVolume',str(cc.bRepBodies.item(0).volume))
 o,c=part('ElectronicsDeck')
 b.add(c,'z',12,[b.poly(ellipse(43,44))],3,'PCA open frame')
 b.cut(c,'z',12,[b.poly(ellipse(35,36))],3,'Core open cooling aperture')
 for side in (-1,1):
  for x,y in pca_holes(side):
   b.add(c,'z',12,[b.cap((x,y),(x,math.copysign(37,y)),3.0)],3,'PCA mount radial bridge')
   b.add(c,'z',15,[b.circ(x,y,2.8)],6,'PCA insulated M2 standoff')
 for x,y in stack:b.add(c,'z',12,[b.cap((x,y),(1.2*x,1.2*y),3.5)],3,'Stack bolt seat bridge')
 for x,y in guards:b.add(c,'z',12,[b.circ(x,y,4)],3,'Core guard pillar seat')
 b.cut(c,'z',12,holes(stack,1.7)+holes(guards,1.2),3,'Chassis and core mounting holes')
 b.cut(c,'z',12,holes(pca_holes(-1)+pca_holes(1),1.2),9,'PCA exact M2 through holes')
 finish(o,'ElectronicsDeck',12)
 for key,z,length in [('LowerSpacer',-26,17),('UpperSpacer',-3,15),('GuardLower',15,23),('GuardUpper',40.4,14.6),('GuardTall',15,40)]:
  o,c=part(key);r=3.5 if 'Spacer' in key else 3.2
  b.add(c,'z',z,[b.circ(0,0,r)],length,'Open core spacer')
  b.cut(c,'z',z,[b.circ(0,0,1.7 if 'Spacer' in key else 1.2)],length,'Metal through bolt clearance')
  finish(o,key,z,6 if 'Spacer' in key else (2 if key=='GuardTall' else 4))
 o,c=part('CoreBridge')
 b.add(c,'z',38,[b.rect(-27.5,-13.5,27.5,13.5)],2.4,'Feather board saddle')
 corners=[(x,y) for x,y in guards if abs(x)>1]
 for x,y in corners:b.add(c,'z',38,[b.cap((math.copysign(25,x),math.copysign(10,y)),(x,y),3.2)],2.4,'Raised bridge arm outside servo plugs')
 for x,y in feather_holes():b.add(c,'z',40.4,[b.circ(x,y,2.8)],4,'Feather exact M2 standoff')
 # Logicbuck insulating cradle: rotated board17.78 x12.7, at y21.5.
 b.add(c,'z',38,[b.rect(-11,13,11,29)],2.4,'Separate logic buck cradle')
 for x in [-9.9,9.9]:b.add(c,'z',40.4,[b.rect(x-1,14.4,x+1,28.6)],2,'Logic buck side rail')
 b.cut(c,'z',38,holes(corners,1.2)+[b.cap((-17,0),(17,0),4),b.cap((-8,26),(8,26),1.2)],2.4,'Vent slots and logic buck retaining strap')
 b.cut(c,'z',38,holes(feather_holes(),1.2),6.4,'Feather M2 through holes')
 finish(o,'CoreBridge',38)
 o,c=part('CoreCap')
 b.add(c,'z',55,[b.poly(ellipse(43.5,44))],2.4,'Removable protective top')
 for x,y in guards:b.add(c,'z',55,[b.circ(x,y,4)],2.4,'Reinforced cap screw boss')
 for y in [-28,-20,-12,0,12,20,28]:
  width=23 if abs(y)>20 else 28
  b.cut(c,'z',55,[b.cap((-width,y),(width,y),1.6)],2.4,'Parallel ventilation slots')
 b.cut(c,'z',55,holes(guards,1.2),2.4,'Removable M2x50 guard fasteners')
 finish(o,'CoreCap',55)

def assemble_core(b):
 def make(key,label):
  o=b.component(label);b.PARTS[key]=o;o.attributes.add('Hexapod','AssemblyLabel',label);return o,o.component
 def purchase(o,parent,rgb):
  o.component.attributes.add('Hexapod','PurchasedEnvelope','Manufacturer PCB mount pattern; connector/SMT simplified')
  b.color(o.component,rgb);b.rigid(parent,o,o.component.name+' mounted')
 def place(key,x,y,label,parent):
  if not hasattr(place,'used'):place.used=set()
  if key not in place.used:
   o=b.PARTS[key];o.transform2=b.matrix(0,0,(x,y,0));place.used.add(key)
   if b.DESIGN.snapshots.hasPendingSnapshot:b.DESIGN.snapshots.add()
  else:o=b.ROOT.occurrences.addExistingComponent(b.PARTS[key].component,b.matrix(0,0,(x,y,0)))
  o.attributes.add('Hexapod','AssemblyLabel',label);b.rigid(parent,o,label+' fixed');return o
 for n,(x,y) in enumerate(guard_points()):
  if abs(x)>1:
   place('GuardLower',x,y,'Core lower guard '+str(n),b.PARTS['ElectronicsDeck'])
   place('GuardUpper',x,y,'Core upper guard '+str(n),b.PARTS['CoreBridge'])
  else:place('GuardTall',x,y,'Core full guard '+str(n),b.PARTS['ElectronicsDeck'])
 for side in (-1,1):
  o,c=make('PCA'+str(side),'PCA9685 #815 | '+('0x40' if side<0 else '0x41'))
  polygon=lambda x0,y0,x1,y1:b.poly([pca_transform(side,x,y) for x,y in [(x0,y0),(x1,y0),(x1,y1),(x0,y1)]])
  b.add(c,'z',21,[polygon(0,0,62.23,25.4)],1.57,'Official PCA PCB envelope')
  b.cut(c,'z',21,[b.circ(x,y,1.25) for x,y in pca_holes(side)],1.57,'Exact PCB mounting holes')
  for x0,x1 in [(5.715,15.875),(18.415,28.575),(33.655,43.815),(46.355,56.515)]:
   # Body and pins envelope; wire socket extends outward beyond bridge, route sideways.
   b.add(c,'z',22.57,[polygon(x0,.127,x1,7.747)],8.41,'Servo signal header envelope')
  b.add(c,'z',22.57,[polygon(27.515,18.19,34.515,25.19)],8.52,'Power terminal nominal envelope')
  purchase(o,b.PARTS['ElectronicsDeck'],(35,118,82))
 o,c=make('Feather','BRAIN | Adafruit Feather ESP32 V2 #5400')
 b.add(c,'z',44.4,[b.rect(-25.4,-11.43,25.4,11.43)],1.57,'Official Feather PCB envelope')
 b.cut(c,'z',44.4,[b.circ(x,y,1.25) for x,y in feather_holes()],1.57,'Feather exact M2 mounting holes')
 b.add(c,'z',45.97,[b.rect(-26.543,-4.47,-19.193,4.47)],3.23,'USB C service port')
 b.add(c,'z',45.97,[b.rect(-18.4145,3.374,-10.4145,10.874)],4.8,'Single cell BAT connector NOT for 2S')
 b.add(c,'z',45.97,[b.rect(-5,-8,19,8)],2.5,'ESP32 shield approximate envelope')
 purchase(o,b.PARTS['CoreBridge'],(45,66,93))
 o,c=make('ServoBuck','POWER | Pololu D42V110F5 #5671')
 b.add(c,'z',-1,[b.rect(-15.875,-21.59,15.875,21.59)],1.6,'Pololu PCB31.75x43.18')
 bh=[(x-15.875,y-21.59) for x,y in [(2.159,2.159),(27.559,2.159),(2.159,41.021),(27.559,41.021)]]
 b.cut(c,'z',-1,[b.circ(x,y,1.09) for x,y in bh],1.6,'Verified regulator M2 hole pattern')
 b.add(c,'z',.6,[b.rect(-10,-13,10,13)],7.4,'9mm regulator overall height envelope')
 purchase(o,b.PARTS['PowerShelf'],(93,101,46))
 o,c=make('LogicBuck','POWER | Pololu D24V10F5 #2831')
 b.add(c,'z',40.4,[b.rect(-8.89,15.15,8.89,27.85)],1.6,'12.7x17.78 logic PCB')
 b.add(c,'z',42,[b.rect(-7,17,7,26)],1.96,'Logic regulator overall3.56height')
 purchase(o,b.PARTS['CoreBridge'],(93,101,46))
 o,c=make('Battery','BATTERY | Gens ace 450mAh 2S XT30 · pouch envelope')
 b.add(c,'z',-26,[b.rect(-21.5,-11.5,21.5,11.5)],13,'Official43x23x13 battery envelope')
 purchase(o,b.PARTS['LowerDeck'],(185,69,47))
 # Exact board-mount bolts, perpendicular deck layers. Pins excluded from simplified boards.
 for key,parent,pts,start,length,seat in [
  ('PCA M2x14',b.PARTS['ElectronicsDeck'],pca_holes(-1)+pca_holes(1),12,14,22.57),
  ('Feather M2x12',b.PARTS['CoreBridge'],feather_holes(),38,12,45.97),
  ('Servo buck M2x10',b.PARTS['PowerShelf'],bh,-6,10,.6)]:
  o=b.hardware_template(key,'z',pts,start,length,seat,2,4);b.rigid(parent,o,key+' fixed')
 # Core cap stack insertedfromunderdeck:15..65 istoo long;45mm gives12..57.
 # M2x45 may be available specialty; use M2x50 with tip62, capnuts57.8..59.4.
 o=b.hardware_template('Core M2x50','z',guard_points(),12,50,57.4,2,4);b.rigid(b.PARTS['ElectronicsDeck'],o,'Removable core guard fasteners')
 b.log('Integrated electronics core mounted with exact PCB hole patterns')
