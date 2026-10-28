"""Fast checks of the generator: servo frame, kinematics, gait and printed solids.

    python -m unittest test_hx18      # about 30 s, needs the CadQuery environment
The full collision sweep runs in build.py and is written to VALIDATION.json.
"""
import itertools
import unittest

import assembly
import gait
import layout
import servo


class ServoFrame(unittest.TestCase):
    def test_vendor_model_lands_in_the_servo_frame(self):
        parts = {p.name: p.shape.BoundingBox() for p in servo.load()}
        horn = parts['drive horn']
        self.assertAlmostEqual(horn.zmax, 0.0, places=2)                       # horn face at z = 0
        self.assertAlmostEqual((horn.xmin + horn.xmax) / 2, 0.0, places=1)     # axis at x = y = 0
        self.assertAlmostEqual((horn.ymin + horn.ymax) / 2, 0.0, places=1)
        case = parts['middle case']
        self.assertAlmostEqual(case.xmin, servo.CASE_X[0], delta=0.1)
        self.assertAlmostEqual(case.xmax, servo.CASE_X[1], delta=0.1)
        self.assertAlmostEqual(parts['idler horn'].zmin, servo.IDLER_HORN_Z[0], places=2)


class Kinematics(unittest.TestCase):
    def test_ik_inverts_fk_in_the_walking_workspace(self):
        # toe outside the hip axis (the IK takes the knee-up, foot-outward branch)
        r = layout.RANGES
        for yaw, hip, knee in itertools.product(r['yaw'], (0.0, 25.0, 60.0), (r['knee'][0], 0.0, 60.0)):
            toe = layout.toe_in_leg_frame(yaw, hip, knee)
            for got, want in zip(layout.leg_ik(toe.x, toe.y, toe.z), (yaw, hip, knee)):
                self.assertAlmostEqual(got, want, places=6)

    def test_stand_pose_has_a_vertical_shank(self):
        tib = layout.frames(0, **layout.STAND)['tibia']
        bend = layout.apply(tib, 0, 0, layout.TIBIA_BEND_Z)
        toe = layout.apply(tib, *layout.TOE)
        self.assertAlmostEqual(bend.x, toe.x, places=6)
        self.assertAlmostEqual(bend.y, toe.y, places=6)
        self.assertAlmostEqual(layout.stand_height(), 125.0, delta=0.5)

    def test_unreachable_target_raises(self):
        with self.assertRaises(ValueError):
            layout.leg_ik(600.0, 0.0, 0.0)


class Gait(unittest.TestCase):
    def test_tripod_stays_inside_the_checked_ranges(self):
        for poses in gait.tripod():
            for pose in poses:
                for value, (lo, hi) in zip(pose, (layout.RANGES[j] for j in assembly.JOINTS)):
                    self.assertTrue(lo <= value <= hi, (pose, lo, hi))

    def test_three_toes_always_on_the_ground(self):
        ground = -layout.stand_height()
        for poses in gait.tripod():
            down = [i for i, (y, h, k) in enumerate(poses)
                    if abs(layout.foot_point(i, y, h, k).z - ground) < 1e-6]
            self.assertGreaterEqual(len(down), 3)


class Solids(unittest.TestCase):
    def test_every_printed_part_is_one_valid_solid(self):
        for name, shape in assembly.shapes().items():
            self.assertTrue(shape.isValid(), name)
            self.assertEqual(len(shape.Solids()), 1, name)

    def test_robot_has_18_servos(self):
        cases = {p.name.split(' / ')[0] for p in assembly.robot() if p.kind == 'servo'}
        self.assertEqual(len(cases), 18)


if __name__ == '__main__':
    unittest.main()
