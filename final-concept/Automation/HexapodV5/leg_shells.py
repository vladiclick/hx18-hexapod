"""V5 centred enclosed arm; generic case inversion, real motor interfaces TBD."""

def _slot(b,c,side,x0,z0,x1,z1,name):
 y=14.0 if side>0 else -16.5
 b.cut(c,'y',y,[b.rect(x0,z0,x1,z1)],2.5,name)

def build(b):
 qty=b.LEG_COUNT
 o=b.component('LEG | Centred proximal clevis');c=o.component
 b.add(c,'z',4,[b.circ(0,0,16)],4.8,'Closed yaw cap')
 b.add(c,'z',4,[b.poly([(0,-16),(16,-14),(34,-20.8),(34,20.8),(16,14),(0,16)])],2.4,'Symmetric short proximal link')
 b.cut(c,'z',4,[b.circ(0,0,13.8)],3.2,'Yaw output coupling reserve')
 for side in (-1,1):
  y=-16.1 if side<0 else 14.3
  b.add(c,'y',y,[b.cap((34,5),(45,-12),4.8)],1.8,'Bilateral internal shoulder support')
  b.add(c,'y',y,[b.circ(45,-12,11.2)],1.8,'Shoulder pivot plate inside upper enclosure')
  b.cut(c,'y',y,[b.circ(45,-12,3.2)],1.8,'Provisional axis/tool access hidden by red upper cover')
 b.register(o,'CoxaCarrier',qty,bed=-23.2)
 o=b.component('LEG | Continuous centred upper enclosure');c=o.component
 b.add(c,'y',-18.7,[b.cap((0,0),(52,0),14)],35.3,'One continuous upper arm outer skin')
 b.cut(c,'y',-16.9,[b.cap((0,0),(52,0),12.2)],33.5,'Two-actuator interior open at front service cover')
 for side in (-1,1):
  _slot(b,c,side,-6,9,22,26,'Narrow fixed shoulder clevis entry slot')
  _slot(b,c,side,18,-30,66,-7,'Narrow lower clevis swept exit slot')
 b.add(c,'z',4.0,[b.rect(22.2,-17.4,29.8,16.6)],8.0,'Upper central retention bridge in actuator gap')
 b.cut(c,'z',4.7,[b.rect(22.4,10,29.6,16.6)],6.8,'Keyed cover tongue pocket')
 b.cut(c,'y',-18.7,[b.circ(26,8.1,1.7)],28.9,'Single central rear service screw path')
 b.cut(c,'y',-18.7,[b.circ(26,8.1,3.1)],1.8,'Flush rear screw head recess')
 b.register(o,'FemurCarrier',qty,'-y',16.6)
 o=b.component('LEG | Full red front service panel');c=o.component
 b.add(c,'y',16.9,[b.cap((0,0),(52,0),14)],1.8,'Closed front panel hides both actuator bodies')
 b.add(c,'z',5.0,[b.rect(22.8,10.2,29.2,17.0)],6.2,'Single keyed internal retention tongue')
 b.cut(c,'y',10.2,[b.circ(26,8.1,2.1)],4.2,'Provisional M3 insert cavity')
 b.register(o,'FemurCheek',qty,'y',10.2);b.color(c,(156,54,46))
 o=b.component('LEG | Centred tapered lower arm');c=o.component
 b.add(c,'y',14.3,[b.circ(0,0,11.2)],1.8,'Internal forward knee pivot plate')
 outline=b.poly([(0,-10),(14,-9),(28,-7.5),(40,-6.5),(40,6.5),(28,7.5),(14,9),(0,10)])
 b.add(c,'y',14.3,[outline],1.8,'Forward inner fork leg')
 b.loft(c,'x',[(38,b.roundrect(-16.1,-6.5,16.1,6.5,1.2)),(48,b.roundrect(-4,-5.5,4,5.5,1.2))],b.F.JoinFeatureOperation,'Symmetric transition into centred lower beam')
 b.add(c,'y',-16.1,[outline],1.8,'Rear inner fork leg linked by transition')
 b.add(c,'y',-16.1,[b.circ(0,0,11.2)],1.8,'Internal rear knee pivot plate')
 b.loft(c,'x',[(48,b.roundrect(-4,-5.5,4,5.5,1.2)),(93,b.roundrect(-3.4,-2.3,3.4,2.3,1.0))],b.F.JoinFeatureOperation,'Slim continuous tapered centred beam')
 for y in (-16.1,14.3):b.cut(c,'y',y,[b.circ(0,0,3.2)],1.8,'Knee axis/tool access concealed by upper service panel')
 b.register(o,'Tibia',qty,'y',-16.1)
 o=b.component('FOOT | Centred soft toe boot');c=o.component
 b.add(c,'y',-5.5,[b.circ(93,0,5.5)],11,'Symmetric compliant toe')
 b.cut(c,'y',-4.6,[b.roundrect(87,-3.2,94.3,3.2,.8)],9.2,'Centred toe socket with clearance; retention TBD')
 b.register(o,'FootPad',qty,'y',-5.5);b.color(c,(225,225,220))
 def reserve(key,lo,hi):
  o=b.component('KEEP-OUT | '+key+' · actuator not selected');c=o.component
  b.add(c,'z',lo[2],[b.rect(lo[0],lo[1],hi[0],hi[1])],hi[2]-lo[2],'Nominal actuator case only')
  b.PARTS[key]=o;c.attributes.add('Hexapod','ReservedEnvelope','Actuator case only; horns bearings ears cables not selected')
 reserve('YawReserve',(-22,-6.5,-28),(10,6.5,-1))
 reserve('HipReserve',(-10,-13.5,-6.5),(22,13.5,6.5))
 reserve('KneeReserve',(30,-13.5,-6.5),(62,13.5,6.5))
