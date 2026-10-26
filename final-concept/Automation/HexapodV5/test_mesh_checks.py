import unittest, numpy as np, sys
sys.modules['networkx']=None
import trimesh
from mesh_checks import bed_orient, component_count
class MeshTests(unittest.TestCase):
 def test_rigid_orientation_preserves_volume_and_puts_base_on_bed(self):
  raw=trimesh.creation.box((10,20,30));raw.apply_translation((7,-13,9))
  for axis,expected in [('z',(10,20,30)),('y',(10,30,20)),('-y',(10,30,20))]:
   result=bed_orient(raw,axis)
   self.assertTrue(np.allclose(result.extents,expected));self.assertAlmostEqual(result.bounds[0][2],0)
   self.assertAlmostEqual(result.volume,raw.volume);self.assertTrue(result.is_watertight)
  self.assertFalse(np.allclose(raw.bounds[0][2],0))
 def test_counts_disjoint_solids(self):
  a=trimesh.creation.box();b=a.copy();b.apply_translation((4,0,0))
  self.assertEqual(component_count(a),1)
  self.assertEqual(component_count(trimesh.util.concatenate((a,b))),2)
 def test_internal_void_is_one_solid_not_two(self):
  outer=trimesh.creation.box((10,10,10));inner=trimesh.creation.box((5,5,5));inner.invert()
  self.assertEqual(component_count(trimesh.util.concatenate((outer,inner))),1)
 def test_rejects_unknown_orientation(self):
  with self.assertRaises(ValueError):bed_orient(trimesh.creation.box(),'x')
