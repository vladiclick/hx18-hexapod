import unittest, math
from core_layout import battery_box, pca_holes, feather_holes, stack_points, pca_transform, guard_points, ellipse
class CoreLayoutTests(unittest.TestCase):
 def test_battery_stack_clearance(self):
  for x,y in stack_points():
   dx=max(abs(x)-23.5,0);dy=max(abs(y)-13.5,0)
   self.assertGreater(math.hypot(dx,dy),3.5+1.0)
 def test_dual_pca_hole_spacing(self):
  for side in (-1,1):
   h=pca_holes(side)
   self.assertAlmostEqual(math.dist(h[0],h[1]),19.05)
   self.assertAlmostEqual(math.dist(h[0],h[2]),55.88)
 def test_outward_servo_header(self):
  for side in (-1,1):
   x,y=pca_transform(side,10,1)
   self.assertGreater(side*y,20)
 def test_feather_mount_pattern(self):
  h=feather_holes();self.assertAlmostEqual(math.dist(h[0],h[1]),17.78)
  self.assertAlmostEqual(math.dist(h[0],h[2]),45.72)
 def test_actual_battery_has_clearance(self):
  self.assertEqual(battery_box(),(43,23,13))
 def test_guard_columns_clear_pcbs(self):
  for x,y in guard_points():
   self.assertAlmostEqual(math.hypot(x,y),42)
   dx=max(abs(x)-31.115,0);dy=max(abs(y)-28.7,0)
   self.assertGreater(math.hypot(dx,dy),3.2+1)
 def test_ellipse_closed_polygon_area(self):
  pts=ellipse(43,44);self.assertEqual(len(pts),48)
  area=sum(x0*y1-x1*y0 for (x0,y0),(x1,y1) in zip(pts,pts[1:]+pts[:1]))/2
  self.assertLess(abs(area/(math.pi*43*44)-1),.003)
if __name__=='__main__':unittest.main()
