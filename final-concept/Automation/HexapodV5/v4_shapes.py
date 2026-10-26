"""Pure 2D outline helpers for the V4 raised-arm shell language.

Coordinates are millimetres. Entity helpers return explicit line and arc
segments so the Fusion builder can create true sketch arcs instead of faceted
polylines where the shape needs a round end or corner.
"""
import math


Point = tuple[float, float]
Entity = tuple[str, tuple]


def _point(point):
    if (
        not isinstance(point, tuple)
        and not isinstance(point, list)
    ) or len(point) != 2:
        raise ValueError("Expected a 2D point")
    x, y = float(point[0]), float(point[1])
    if not math.isfinite(x) or not math.isfinite(y):
        raise ValueError("Point coordinates must be finite")
    return (x, y)


def _positive(value, name):
    value = float(value)
    if not math.isfinite(value) or value <= 0:
        raise ValueError(name + " must be positive")
    return value


def _add(a, b):
    return (a[0] + b[0], a[1] + b[1])


def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1])


def _mul(a, scale):
    return (a[0] * scale, a[1] * scale)


def _length(v):
    return math.hypot(v[0], v[1])


def _unit(v):
    length = _length(v)
    if length <= 1e-9:
        raise ValueError("Degenerate vector")
    return (v[0] / length, v[1] / length)


def _lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def capsule_entities(a, b, r):
    """Return a closed capsule loop as line/arc sketch entities."""
    a = _point(a)
    b = _point(b)
    r = _positive(r, "Capsule radius")
    direction = _sub(b, a)
    u = _unit(direction)
    n = (-u[1], u[0])
    a_left = _add(a, _mul(n, r))
    b_left = _add(b, _mul(n, r))
    b_right = _sub(b, _mul(n, r))
    a_right = _sub(a, _mul(n, r))
    return (
        ("line", (a_left, b_left)),
        ("arc", (b_left, _add(b, _mul(u, r)), b_right)),
        ("line", (b_right, a_right)),
        ("arc", (a_right, _sub(a, _mul(u, r)), a_left)),
    )


def rounded_rect_entities(x0, y0, x1, y1, r):
    """Return a clockwise rounded rectangle loop as line/arc entities."""
    x0, y0, x1, y1 = map(float, (x0, y0, x1, y1))
    if not all(math.isfinite(v) for v in (x0, y0, x1, y1)):
        raise ValueError("Rectangle coordinates must be finite")
    if x1 <= x0 or y1 <= y0:
        raise ValueError("Rectangle must have positive width and height")
    r = _positive(r, "Corner radius")
    if r > min((x1 - x0) / 2, (y1 - y0) / 2):
        raise ValueError("Corner radius is too large")
    q = r / math.sqrt(2)
    return (
        ("line", ((x0 + r, y0), (x1 - r, y0))),
        ("arc", ((x1 - r, y0), (x1 - r + q, y0 + r - q), (x1, y0 + r))),
        ("line", ((x1, y0 + r), (x1, y1 - r))),
        ("arc", ((x1, y1 - r), (x1 - r + q, y1 - r + q), (x1 - r, y1))),
        ("line", ((x1 - r, y1), (x0 + r, y1))),
        ("arc", ((x0 + r, y1), (x0 + r - q, y1 - r + q), (x0, y1 - r))),
        ("line", ((x0, y1 - r), (x0, y0 + r))),
        ("arc", ((x0, y0 + r), (x0 + r - q, y0 + r - q), (x0 + r, y0))),
    )


def _bezier(p0, p1, p2, p3, t):
    mt = 1.0 - t
    return (
        mt**3 * p0[0] + 3 * mt**2 * t * p1[0] + 3 * mt * t**2 * p2[0] + t**3 * p3[0],
        mt**3 * p0[1] + 3 * mt**2 * t * p1[1] + 3 * mt * t**2 * p2[1] + t**3 * p3[1],
    )


def _bezier_tangent(p0, p1, p2, p3, t):
    mt = 1.0 - t
    return (
        3 * mt**2 * (p1[0] - p0[0])
        + 6 * mt * t * (p2[0] - p1[0])
        + 3 * t**2 * (p3[0] - p2[0]),
        3 * mt**2 * (p1[1] - p0[1])
        + 6 * mt * t * (p2[1] - p1[1])
        + 3 * t**2 * (p3[1] - p2[1]),
    )


def _centreline(t):
    return _bezier((12.0, 5.0), (35.0, 18.0), (72.0, 15.0), (93.0, 0.0), t)


def _normal(t):
    tangent = _unit(_bezier_tangent((12.0, 5.0), (35.0, 18.0), (72.0, 15.0), (93.0, 0.0), t))
    return (-tangent[1], tangent[0])


def _ribbon(t0, t1, samples, half_width):
    if samples < 40:
        raise ValueError("At least 40 samples are required")
    if not (0 <= t0 < t1 <= 1):
        raise ValueError("Invalid ribbon parameter range")
    left = []
    right = []
    for i in range(samples):
        t = t0 + (t1 - t0) * i / (samples - 1)
        center = _centreline(t)
        normal = _normal(t)
        width = half_width(t)
        if not math.isfinite(width) or width <= 0:
            raise ValueError("Invalid half width")
        left.append(_add(center, _mul(normal, width)))
        right.append(_sub(center, _mul(normal, width)))
    return tuple(left + list(reversed(right)))


def blade_outline(samples=56, extra=0.0):
    """Closed curved raised-arm blade outline.

    The returned polygon is intended to be closed by the sketch builder from
    the last point back to the first point. The centreline is a fixed cubic
    Bezier: (12,5), (35,18), (72,15), (93,0).
    """
    extra = float(extra)
    if not math.isfinite(extra) or extra < 0:
        raise ValueError("extra clearance must be finite and non-negative")
    return _ribbon(
        0.0,
        1.0,
        int(samples),
        lambda t: 8.0 + (2.5 - 8.0) * t + extra,
    )


def blade_window(samples=44):
    """Thin through-cut window inside the raised-arm blade."""
    def half_width(t):
        local = (t - 0.2) / 0.62
        taper = math.sin(math.pi * local)
        return 1.0 + max(0.0, taper) * 1.0

    return _ribbon(0.2, 0.82, int(samples), half_width)
