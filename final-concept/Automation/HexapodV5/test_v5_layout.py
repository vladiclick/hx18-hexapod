import math
import unittest

from v5_layout import layout, case_fits, transition_clearance


class InlineLayoutTests(unittest.TestCase):
    def test_all_symmetric_named_envelopes_keep_midplane(self):
        p = layout()
        for name, lo, hi in p['centred_envelopes']:
            self.assertAlmostEqual((lo[1] + hi[1]) / 2, 0, msg=name)
        self.assertEqual(p['foot_lateral'], 0)

    def test_nominal_angles_and_capsule_values_are_v5_inline_values(self):
        p = layout()
        self.assertEqual(p['femur_length'], 52)
        self.assertEqual(p['femur_neutral_deg'], 55)
        self.assertEqual(p['tibia_length'], 93)
        self.assertEqual(p['tibia_abs_deg'], -72)
        self.assertEqual(p['outer_capsule_start'], (0, 0))
        self.assertEqual(p['outer_capsule_end'], (52, 0))
        self.assertEqual(p['outer_capsule_radius'], 14)
        self.assertEqual(p['shell_capsule_radius'], 14)
        self.assertEqual(p['internal_radius'], 12.2)
        self.assertEqual(p['shell_y_half'], 18.7)
        self.assertEqual(p['inner_cavity_y_half'], 16.9)

    def test_cases_fit_inside_internal_cavity_with_bridge_between_them(self):
        p = layout()
        for lo, hi in p['cases']:
            self.assertTrue(case_fits(lo, hi))
            self.assertEqual((lo[1], hi[1]), (-13.5, 13.5))
        self.assertGreaterEqual(p['cases'][1][0][0] - p['cases'][0][1][0], 6)
        self.assertGreater(p['bridge_x_min'], p['cases'][0][1][0])
        self.assertLess(p['bridge_x_max'], p['cases'][1][0][0])
        self.assertEqual(p['hip_case'], ((-10, -13.5, -6.5), (22, 13.5, 6.5)))
        self.assertEqual(p['knee_case'], ((30, -13.5, -6.5), (62, 13.5, 6.5)))

    def test_yoke_plates_are_internal_with_clearance_to_cases_skin_and_cap(self):
        p = layout()
        self.assertEqual(p['yoke_plate_inner_y'], 14.3)
        self.assertEqual(p['yoke_plate_outer_y'], 16.1)
        self.assertAlmostEqual(p['yoke_plate_thickness'], 1.8)
        self.assertAlmostEqual(p['yoke_case_gap'], 0.8)
        self.assertAlmostEqual(p['yoke_skin_gap'], 0.8)
        self.assertEqual(p['yoke_cap_radius'], 11.2)
        self.assertAlmostEqual(p['yoke_radial_gap'], 1.0)
        self.assertEqual(
            p['yoke_plates'],
            [((-10, -16.1, -11.2), (62, -14.3, 11.2)), ((-10, 14.3, -11.2), (62, 16.1, 11.2))],
        )

    def test_insert_bridge_is_top_side_not_lower_fork_obstruction(self):
        p = layout()
        self.assertEqual(p['bridge_x_center'], 26)
        self.assertAlmostEqual((p['bridge_x_min'] + p['bridge_x_max']) / 2, p['bridge_x_center'])
        self.assertEqual((p['bridge_x_min'], p['bridge_x_max']), (22.2, 29.8))
        self.assertEqual((p['bridge_y_min'], p['bridge_y_max']), (-17.4, 16.6))
        self.assertEqual((p['bridge_z_min'], p['bridge_z_max']), (4, 12))
        self.assertEqual(p['retention_pocket_z'], (4.7, 11.5))
        self.assertEqual(p['red_tongue_z'], (5.0, 11.2))
        self.assertEqual(p['m3_insert_center_z'], 8.1)
        self.assertEqual(p['m3_insert_radius'], 2.1)
        self.assertGreater(p['bridge_z_min'], 0)
        self.assertGreaterEqual(p['m3_insert_center_z'] - p['m3_insert_radius'] - p['red_tongue_z'][0], 1.0)
        self.assertGreaterEqual(p['red_tongue_z'][1] - (p['m3_insert_center_z'] + p['m3_insert_radius']), 1.0)

    def test_lower_transition_tapers_to_closed_blade_end(self):
        p = layout()
        self.assertEqual(p['transition_start'], (38, 16.1, 6.5))
        self.assertEqual(p['transition_taper'], (48, 4, 5.5))
        self.assertEqual(p['blade_end'], (93, 3.4, 2.3))

    def test_forecover_and_carrier_envelopes_cover_red_cap_without_disc_protrusion(self):
        p = layout()
        self.assertEqual(p['red_forecover_y'], (16.9, 18.7))
        self.assertEqual(p['carrier_y'], (-18.7, 16.6))
        self.assertGreaterEqual(p['red_forecover_y'][0], p['inner_cavity_y_half'])
        self.assertLessEqual(p['red_forecover_y'][1], p['shell_y_half'])
        self.assertAlmostEqual(p['carrier_y'][0], -p['shell_y_half'])

    def test_root_and_knee_fork_slots_are_paired_inside_skin(self):
        p = layout()
        self.assertEqual(p['fork_slot_y_band'], (14, 16.5))
        self.assertEqual(
            p['coxa_fork_entry_slots'],
            [((-6, -16.5, 9), (22, -14, 26)), ((-6, 14, 9), (22, 16.5, 26))],
        )
        self.assertEqual(
            p['knee_fork_exit_slots'],
            [((18, -16.5, -30), (66, -14, -7)), ((18, 14, -30), (66, 16.5, -7))],
        )
        for slots in (p['coxa_fork_entry_slots'], p['knee_fork_exit_slots']):
            for lo, hi in slots:
                self.assertLessEqual(max(abs(lo[1]), abs(hi[1])), p['inner_cavity_y_half'])

    def test_forecap_screw_and_keyed_tongue_are_declared(self):
        p = layout()
        self.assertEqual(
            p['forecap_screw_axis'],
            {'axis': 'Y', 'x': 26, 'z': 8.1, 'y_start': -16.9, 'y_end': 13.1, 'length': 30.0},
        )
        self.assertEqual(p['forecap_key_tongue_y'], (10.2, 17.0))
        self.assertEqual(p['forecap_key_tongue_z'], (5.0, 11.2))
        self.assertAlmostEqual(p['forecap_key_tongue_z'][1] - p['forecap_key_tongue_z'][0], 6.2)

    def test_full_knee_range_clears_closed_femur_shell(self):
        clearances = [transition_clearance(knee) for knee in range(-15, 16)]
        self.assertGreater(min(clearances), 2)
        self.assertAlmostEqual(
            transition_clearance(-15),
            abs(38 * math.sin(math.radians(-142)) + 6.5 * abs(math.cos(math.radians(-142)))) - 14,
        )

    def test_case_fit_rejects_invalid_or_outside_boxes(self):
        with self.assertRaises(ValueError):
            case_fits((0, 0, 0), (1, 1, float('nan')))
        with self.assertRaises(ValueError):
            case_fits((0, 0, 0), (0, 1, 1))
        self.assertFalse(case_fits((-20, -13.5, -6.5), (22, 13.5, 6.5)))
        self.assertFalse(case_fits((-10, -17.1, -6.5), (22, 17.1, 6.5)))
        self.assertFalse(case_fits((-10, -13.5, -6.5), (22, 14.5, 6.5)))

    def test_transition_clearance_validates_input(self):
        with self.assertRaises(ValueError):
            transition_clearance(float('inf'))
        with self.assertRaises(ValueError):
            transition_clearance('0')

    def test_service_note_does_not_claim_drop_in_replacement(self):
        self.assertIn('requires unbolting the joint axes', layout()['service_note'])


if __name__ == '__main__':
    unittest.main()
