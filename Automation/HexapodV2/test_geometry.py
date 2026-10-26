import unittest, math
from geometry import transform, position, stance, validate, capsule, DEFAULT
class GeometryTests(unittest.TestCase):
 def test_right_handed_frames(self):
  for a in range(0,360,60):
   for p in [-95,-25,0]:
    m=transform(a,p,(1,2,3))
    cols=[tuple(m[r][c] for r in range(3)) for c in range(3)]
    for c in cols: self.assertAlmostEqual(sum(v*v for v in c),1)
    self.assertAlmostEqual(sum(cols[0][i]*cols[1][i] for i in range(3)),0)
    cross=(cols[0][1]*cols[1][2]-cols[0][2]*cols[1][1],cols[0][2]*cols[1][0]-cols[0][0]*cols[1][2],cols[0][0]*cols[1][1]-cols[0][1]*cols[1][0])
    for i in range(3):self.assertAlmostEqual(cross[i],cols[2][i])
 def test_mm_translation(self):
  m=transform(0,0,(100,20,-30));self.assertEqual(m[0][3],10);self.assertEqual(m[2][3],-3)
 def test_leg_stance(self):
  for a in range(0,360,60):
   s,k,f=stance(a)
   self.assertAlmostEqual(math.dist(s,k),42)
   self.assertAlmostEqual(math.dist(k,f),80)
   self.assertLess(f[2],-54)
   self.assertLess(math.hypot(f[0]-s[0],f[1]-s[1]),35)
 def test_invalid_parameters(self):
  for key,value in [('femur',0),('servo_width',-1),('plate',0),('yaw_radius',25)]:
   with self.assertRaises(ValueError):validate(dict(DEFAULT,**{key:value}))
 def test_default_parameters(self):self.assertIsNone(validate(DEFAULT))
 def test_nonfinite_parameters(self):
  for value in [float('inf'),float('nan'),'large']:
   with self.assertRaises(ValueError):validate(dict(DEFAULT,plate=value))
 def test_negative_capsule_radius(self):
  with self.assertRaises(ValueError):capsule((0,0),(1,0),-1)
 def test_capsule_closed_without_duplicate(self):
  pts=capsule((0,0),(20,0),3)
  self.assertGreater(len(pts),12);self.assertNotEqual(pts[0],pts[-1])
  self.assertAlmostEqual(max(x for x,y in pts),23)
  self.assertAlmostEqual(min(x for x,y in pts),-3)
 def test_capsule_rotation(self):
  pts=capsule((0,0),(0,20),3)
  self.assertAlmostEqual(max(y for x,y in pts),23)
 def test_degenerate_capsule(self):
  with self.assertRaises(ValueError):capsule((0,0),(0,0),3)
 def test_position(self):
  self.assertEqual(position(0,10,2,3),(10,2,3))
  p=position(90,10,2,3);self.assertAlmostEqual(p[0],-2);self.assertAlmostEqual(p[1],10)
if __name__=='__main__':unittest.main()
