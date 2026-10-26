import math
import unittest

from v4_shapes import (
    blade_outline,
    blade_window,
    capsule_entities,
    rounded_rect_entities,
)


def _dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _finite_point(point):
    return (
        len(point) == 2
        and all(isinstance(value, (int, float)) for value in point)
        and all(math.isfinite(value) for value in point)
    )


def _entity_points(entities):
    points = []
    for kind, payload in entities:
        if kind == "line":
            start, end = payload
            points.extend((start, end))
        elif kind == "arc":
            start, mid, end = payload
            points.extend((start, mid, end))
        else:
            raise AssertionError("unknown entity kind " + repr(kind))
    return points


def _turn(a, b, c):
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def _segments_cross(a, b, c, d):
    if max(a[0], b[0]) < min(c[0], d[0]) or max(c[0], d[0]) < min(a[0], b[0]):
        return False
    if max(a[1], b[1]) < min(c[1], d[1]) or max(c[1], d[1]) < min(a[1], b[1]):
        return False
    ab_c = _turn(a, b, c)
    ab_d = _turn(a, b, d)
    cd_a = _turn(c, d, a)
    cd_b = _turn(c, d, b)
    return ab_c * ab_d < -1e-9 and cd_a * cd_b < -1e-9


def _closed_segments(points):
    return [(points[i], points[(i + 1) % len(points)]) for i in range(len(points))]


def _assert_simple_polygon(testcase, points):
    testcase.assertGreaterEqual(len(points), 40)
    testcase.assertTrue(all(_finite_point(point) for point in points))
    testcase.assertNotEqual(points[0], points[-1])
    segments = _closed_segments(points)
    for i, first in enumerate(segments):
        for j, second in enumerate(segments):
            if abs(i - j) <= 1 or {i, j} == {0, len(segments) - 1}:
                continue
            testcase.assertFalse(
                _segments_cross(first[0], first[1], second[0], second[1]),
                (i, j, first, second),
            )


class EntityShapeTests(unittest.TestCase):
    def test_capsule_entities_are_continuous_true_arcs(self):
        entities = capsule_entities((0, 0), (20, 0), 3)
        self.assertEqual([kind for kind, _ in entities], ["line", "arc", "line", "arc"])
        for (_, payload), (_, next_payload) in zip(entities, entities[1:] + entities[:1]):
            self.assertEqual(payload[-1], next_payload[0])
        self.assertTrue(all(_finite_point(point) for point in _entity_points(entities)))
        for arc in (entities[1][1], entities[3][1]):
            start, mid, end = arc
            center = (20, 0) if mid[0] > 10 else (0, 0)
            self.assertAlmostEqual(_dist(start, center), 3)
            self.assertAlmostEqual(_dist(mid, center), 3)
            self.assertAlmostEqual(_dist(end, center), 3)

    def test_capsule_rejects_invalid_input(self):
        for args in [((0, 0), (0, 0), 3), ((0, 0), (1, 0), 0), ((0, 0), (1, 0), -1)]:
            with self.assertRaises(ValueError):
                capsule_entities(*args)

    def test_rounded_rect_entities_are_continuous_and_radius_correct(self):
        entities = rounded_rect_entities(-10, -5, 20, 15, 4)
        self.assertEqual(len(entities), 8)
        self.assertEqual([kind for kind, _ in entities].count("arc"), 4)
        for (_, payload), (_, next_payload) in zip(entities, entities[1:] + entities[:1]):
            self.assertEqual(payload[-1], next_payload[0])
        for point in _entity_points(entities):
            self.assertTrue(_finite_point(point))
            self.assertGreaterEqual(point[0], -10)
            self.assertLessEqual(point[0], 20)
            self.assertGreaterEqual(point[1], -5)
            self.assertLessEqual(point[1], 15)
        centers = [(16, -1), (16, 11), (-6, 11), (-6, -1)]
        arcs = [payload for kind, payload in entities if kind == "arc"]
        for center, arc in zip(centers, arcs):
            for point in arc:
                self.assertAlmostEqual(_dist(point, center), 4)

    def test_rounded_rect_rejects_invalid_input(self):
        invalid = [
            (0, 0, 1, 1, 0),
            (0, 0, 1, 1, -1),
            (0, 0, 1, 1, 0.6),
            (1, 0, 0, 1, 0.1),
            (0, 1, 1, 0, 0.1),
        ]
        for args in invalid:
            with self.assertRaises(ValueError):
                rounded_rect_entities(*args)


class BladeShapeTests(unittest.TestCase):
    def test_blade_outline_is_deterministic_finite_and_simple(self):
        first = blade_outline()
        second = blade_outline()
        self.assertEqual(first, second)
        _assert_simple_polygon(self, first)
        xs = [point[0] for point in first]
        ys = [point[1] for point in first]
        self.assertGreaterEqual(max(xs), 93)
        self.assertGreater(max(ys) - min(ys), 15)
        self.assertAlmostEqual(_dist(first[0], first[-1]), 16.0, places=6)
        self.assertAlmostEqual(_dist(first[len(first) // 2 - 1], first[len(first) // 2]), 5.0, places=6)

    def test_blade_outline_extra_adds_clearance_without_changing_centreline(self):
        base = blade_outline()
        clearance = blade_outline(extra=0.4)
        _assert_simple_polygon(self, clearance)
        self.assertEqual(len(base), len(clearance))
        self.assertAlmostEqual(_dist(clearance[0], clearance[-1]), 16.8, places=6)
        self.assertAlmostEqual(
            _dist(clearance[len(clearance) // 2 - 1], clearance[len(clearance) // 2]),
            5.8,
            places=6,
        )
        for left, right, wide_left, wide_right in zip(
            base[: len(base) // 2],
            reversed(base[len(base) // 2 :]),
            clearance[: len(clearance) // 2],
            reversed(clearance[len(clearance) // 2 :]),
        ):
            base_mid = ((left[0] + right[0]) / 2, (left[1] + right[1]) / 2)
            wide_mid = ((wide_left[0] + wide_right[0]) / 2, (wide_left[1] + wide_right[1]) / 2)
            self.assertLess(_dist(base_mid, wide_mid), 1e-9)
            self.assertAlmostEqual(_dist(wide_left, wide_right) - _dist(left, right), 0.8, places=6)

    def test_blade_window_is_inside_blade_and_tapered(self):
        outline = blade_outline()
        window = blade_window()
        _assert_simple_polygon(self, window)
        outline_x = [point[0] for point in outline]
        outline_y = [point[1] for point in outline]
        for point in window:
            self.assertGreater(point[0], min(outline_x))
            self.assertLess(point[0], max(outline_x))
            self.assertGreater(point[1], min(outline_y))
            self.assertLess(point[1], max(outline_y))
        self.assertLess(_dist(window[0], window[-1]), 5.0)
        self.assertGreater(_dist(window[len(window) // 4], window[-len(window) // 4 - 1]), 3.5)

    def test_blade_rejects_low_sample_counts(self):
        with self.assertRaises(ValueError):
            blade_outline(samples=20)
        with self.assertRaises(ValueError):
            blade_window(samples=20)
        for extra in (-0.1, math.nan, math.inf):
            with self.assertRaises(ValueError):
                blade_outline(extra=extra)


if __name__ == "__main__":
    unittest.main()
