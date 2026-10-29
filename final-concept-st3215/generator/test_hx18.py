"""python -m unittest test_hx18"""
import csv
import math
import unittest
from pathlib import Path

import cadquery as cq

import gait
import layout
import parts as P

CONCEPT_BOM = Path(__file__).resolve().parents[2] / 'final-concept' / 'PRINT-BOM.csv'


class Concept(unittest.TestCase):
    def test_parts_match_the_final_concept(self):
        """servo=False at scale 1 rebuilds the eight concept parts (volumes Fusion reported)."""
        with open(CONCEPT_BOM) as f:
            ref = {r['part']: float(r['single_volume_cm3']) for r in csv.DictReader(f)}
        for key, fn in P.PRINTS.items():
            vol = fn(1.0, servo=False).solid().Volume() / 1000
            self.assertAlmostEqual(vol, ref[key], delta=1e-4, msg=key)

    def test_layout_is_the_concept_scaled(self):
        self.assertAlmostEqual(layout.FEMUR, 52 * layout.S)
        _, shoulder, knee = layout.joints(0, s=1.0)
        self.assertAlmostEqual(shoulder[0], 49 + 45)
        self.assertAlmostEqual(shoulder[2], -12)
        self.assertAlmostEqual(math.dist(shoulder, knee), 52)


class Servo(unittest.TestCase):
    def test_two_cases_fit_between_hip_and_knee(self):
        hip_end = 35.1                           # servo.CASE_X[1]
        knee_end = layout.FEMUR - 35.1
        self.assertGreater(knee_end - hip_end, 2.0)

    def test_case_corner_fits_the_capsule(self):
        corner = math.hypot(10.15, 12.36)        # case end behind the output axis
        self.assertLess(corner, 12.2 * layout.S - 1.0)

    def test_horn_faces_inside_the_plates(self):
        self.assertLess(layout.HORN_Y, 14.3 * layout.S)   # bosses bridge the gap to the plates

    def test_frames(self):
        f = layout.frames(2, 10, 5, -7)
        _, shoulder, knee = layout.joints(2, 10, 5, -7)
        self.assertLess((layout.apply(f['femur'], layout.FEMUR) - cq.Vector(*knee)).Length, 1e-9)
        self.assertLess((layout.apply(f['femur']) - cq.Vector(*shoulder)).Length, 1e-9)


class Gait(unittest.TestCase):
    def test_ik_inverts_the_frames(self):
        for i, q in ((0, (8.0, 12.0, -9.0)), (4, (-5.0, -4.0, 11.0))):
            got = gait.ik(i, layout.foot_point(i, *q).toTuple())
            for a, b in zip(got, q):
                self.assertAlmostEqual(a, b, places=9)

    def test_planted_feet_do_not_slide(self):
        cycle = gait.tripod()
        for i in range(layout.LEGS):
            home_z = layout.foot_point(i).z
            planted = [(n, layout.foot_point(i, *poses[i]) + cq.Vector(bx, by, 0))
                       for n, ((bx, by), poses) in enumerate(cycle)
                       if abs(layout.foot_point(i, *poses[i]).z - home_z) < 1e-9]
            for (n0, p0), (n1, p1) in zip(planted, planted[1:]):
                if n1 == n0 + 1:
                    self.assertLess((p1 - p0).Length, 1e-9)


class Solids(unittest.TestCase):
    def test_every_print_part_is_one_valid_solid(self):
        for key, fn in P.PRINTS.items():
            self.assertTrue(fn().solid().isValid(), key)


if __name__ == '__main__':
    unittest.main()
