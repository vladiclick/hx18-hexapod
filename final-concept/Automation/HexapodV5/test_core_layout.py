import math
import unittest
from v3_core_layout import (lid_fasteners, cassette_fasteners, yaw_case_distance,
                         island_clearance, core_dimensions, electronics_reserves)


class CoreLayoutTests(unittest.TestCase):
    def test_four_lid_fasteners_clear_yaw_cases_and_hubs(self):
        self.assertEqual(len(lid_fasteners()), 4)
        for x, y in lid_fasteners():
            self.assertGreater(min(yaw_case_distance((x, y), n) for n in range(6)), 6.5)
            self.assertGreater(min(math.hypot(x-49*math.cos(n*math.pi/3),
                                             y-49*math.sin(n*math.pi/3))
                                   for n in range(6)), 16.8+6.5)

    def test_two_cassette_posts_do_not_touch_yaw_cases_or_battery(self):
        self.assertEqual(len(cassette_fasteners()), 2)
        for x, y in cassette_fasteners():
            self.assertGreater(min(yaw_case_distance((x, y), n) for n in range(6)), 3.5)
            self.assertGreater(abs(y)-11.5, 3.5)

    def test_electronics_reserve_corners_clear_island(self):
        for item in electronics_reserves():
            if item['key'] != 'BatteryReserve':
                self.assertGreater(island_clearance(item), 0.3)
                self.assertLessEqual(item['z']+item['height'], 8)

    def test_low_rim_and_island_clear_neutral_yaw_hub(self):
        dims = core_dimensions()
        self.assertLess(dims['rim_top'], 4)
        self.assertGreater(49-16-dims['island_radius'], 1)
        self.assertGreaterEqual(dims['island_top']-2.4-8, 1.9)

    def test_rotated_regulator_clears_all_six_yaw_bays(self):
        reg=next(x for x in electronics_reserves() if x['key']=='RegulatorReserve')
        a=math.radians(reg['angle'])
        points=[(x*math.cos(a)-y*math.sin(a),x*math.sin(a)+y*math.cos(a)) for x in (-17,17) for y in (-22,22)]
        for n in range(6):
            angle=n*math.pi/3
            self.assertGreater(27-max(x*math.cos(angle)+y*math.sin(angle) for x,y in points),1.2)
        for x in (-25,25):
            for y in (-4,4):
                projected=abs(x*math.cos(a)+y*math.sin(a))-.8*(math.cos(a)+math.sin(a))
                self.assertGreater(projected-17,1.5)

    def test_reserves_are_explicitly_unconfirmed(self):
        for item in electronics_reserves():
            self.assertEqual(item['status'], 'reserved envelope; component not selected')


if __name__ == '__main__':
    unittest.main()
