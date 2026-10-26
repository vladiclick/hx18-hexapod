import math
DEFAULT={'yaw_radius':49.,'coxa':45.,'femur':52.,'tibia':93.,'shoulder_z':-12.,'femur_angle':55.,'tibia_angle':-72.,'plate':3.,'foot_lateral':0.}
def validate(p):
 for k in ['yaw_radius','coxa','femur','tibia','plate']:
  if not isinstance(p[k],(int,float)) or not math.isfinite(p[k]) or p[k]<=0:raise ValueError('Invalid '+k)
 if not isinstance(p['shoulder_z'],(int,float)) or not math.isfinite(p['shoulder_z']):raise ValueError('Invalid shoulder_z')
 if p['yaw_radius']<40:raise ValueError('Servo pockets overlap the central opening')
def position(a,x,y,z):
 r=math.radians(a);return (math.cos(r)*x-math.sin(r)*y,math.sin(r)*x+math.cos(r)*y,z)
def transform(yaw,pitch,origin):
 a,b=map(math.radians,(yaw,pitch));ca,sa,cb,sb=math.cos(a),math.sin(a),math.cos(b),math.sin(b)
 return [[ca*cb,-sa,-ca*sb,origin[0]/10],[sa*cb,ca,-sa*sb,origin[1]/10],[sb,0,cb,origin[2]/10],[0,0,0,1]]
def stance(a,p=DEFAULT):
 validate(p)
 s=position(a,p['yaw_radius']+p['coxa'],0,p['shoulder_z'])
 fa,ta=map(math.radians,(p['femur_angle'],p['tibia_angle']))
 k=position(a,p['yaw_radius']+p['coxa']+p['femur']*math.cos(fa),0,p['shoulder_z']+p['femur']*math.sin(fa))
 f=position(a,p['yaw_radius']+p['coxa']+p['femur']*math.cos(fa)+p['tibia']*math.cos(ta),0,p['shoulder_z']+p['femur']*math.sin(fa)+p['tibia']*math.sin(ta))
 return s,k,f
def capsule(a,b,r,n=24):
 if math.dist(a,b)<1e-6 or r<=0:raise ValueError('Invalid capsule')
 ang=math.atan2(b[1]-a[1],b[0]-a[0]);out=[]
 for c,start in [(b,ang-math.pi/2),(a,ang+math.pi/2)]:
  for i in range(n+1):
   t=start+i*math.pi/n;out.append((c[0]+r*math.cos(t),c[1]+r*math.sin(t)))
 return out

def foot(a,yaw,hip,knee,p=DEFAULT):
 h=math.radians(p['femur_angle']+hip)
 t=math.radians(p['tibia_angle']+hip+knee)
 r=p['coxa']+p['femur']*math.cos(h)+p['tibia']*math.cos(t)
 local=position(a-yaw,r,p['foot_lateral'],p['shoulder_z']+p['femur']*math.sin(h)+p['tibia']*math.sin(t))
 pivot=position(a,p['yaw_radius'],0,0)
 return tuple(local[i]+pivot[i] for i in range(3))
