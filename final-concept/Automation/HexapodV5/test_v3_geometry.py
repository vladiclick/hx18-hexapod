import unittest, math
from v3_geometry import DEFAULT, stance, foot, capsule, validate

class GeometryChecks(unittest.TestCase):
    def test_neutral_fk_matches_link_dimensions(self):
        p=DEFAULT
        s,k,f=stance(0)
        self.assertEqual(s,(94,0,-12))
        self.assertAlmostEqual(k[0]-s[0],52*math.cos(math.radians(55)))
        expected=(f[0],0,f[2])
        for a,b in zip(foot(0,0,0,0),expected):self.assertAlmostEqual(a,b)
    def test_every_leg_is_radial_rotation(self):
        for a in range(0,360,60):
            f=foot(a,0,0,0)
            self.assertAlmostEqual(math.hypot(f[0],f[1]),math.hypot(*foot(0,0,0,0)[:2]))
    def test_yaw_rotates_about_joint_and_not_body_centre(self):
        local=foot(0,0,0,0)[0]-49
        moved=foot(0,90,0,0)
        self.assertAlmostEqual(moved[0],49)
        self.assertAlmostEqual(moved[1],-local)
    def test_invalid_geometry(self):
        for key in ('coxa','femur','tibia','plate'):
            for value in (0,-1,math.nan,math.inf,'wrong'):
                with self.assertRaises(ValueError):validate(dict(DEFAULT,**{key:value}))
        with self.assertRaises(ValueError):validate(dict(DEFAULT,yaw_radius=30))
    def test_capsule_closed_boundary(self):
        for a,b,r in (((0,0),(42,0),16),((12,38),(38,38),12)):
            points=capsule(a,b,r)
            self.assertGreater(len(points),24)
            self.assertAlmostEqual(max(p[0] for p in points),b[0]+r)
        for a,b,r in (((0,0),(0,0),1),((0,0),(1,0),0)):
            with self.assertRaises(ValueError):capsule(a,b,r)

if __name__=='__main__':unittest.main()
