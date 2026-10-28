"""The eight print parts of the HX18 final concept, with room for the Waveshare ST3215.

Every outline and feature is the one in final-concept/Automation/HexapodV5
(leg_shells.py, core_enclosure.py), in the same order, scaled by layout.S. With
servo=False and s=1 these functions rebuild the original parts exactly; test_hx18
checks that against the volumes Fusion reported for them.

What changes for the servo (servo=True), all of it inside the parts:
  - coxa: a hub under the yaw cap down to the yaw servo's horn; horn bosses on the
    two shoulder plates; M3 horn screw holes
  - femur: the retention bridge moves above the servos and gets a twin below them;
    the cover screw passes over the servos; M2 standoffs hold the servo cases
  - femur cover: the tongue moves in front of the servos
  - tibia: horn bosses and M3 horn screw holes on the knee plates
  - core tub: two M2 standoffs per yaw servo on the floor; battery strap slots and
    the cassette screw columns move clear of the servos
  - electronics cassette: bays for the yaw servos; supports moved to match
Screws, inserts and their holes keep their real size.
"""
import math

from geometry import Part, cap, circ, poly, rect, roundrect
import layout
from layout import HORN_Y, S, YAW_HORN_Z
from v3_core_layout import lid_fasteners, rounded_hex  # from the concept, via geometry's path

# real hardware sizes
M3_CLEAR, M3_HEAD, M3_INSERT = 1.7, 3.1, 2.1
M2_CLEAR, M2_HEAD = 1.1, 2.1
HORN_SCREW_R = 7.0          # ST3215 horn: 4 x M3 on a 14 mm circle
HORN_BOSS_R = 10.4          # horn radius 9.6 + 0.8
AXIS_HOLE_R = 3.5           # clears the 3 mm idler bushing; tool access to the horn screw
HORN_COUNTERBORE = 1.8      # M3 button head (1.65 mm) sits below the plate surface

# ST3215 case, servo frame (servo.py): screw holes in the bottom face, used at the far end
CASE_SCREW = (32.8, 10.2)
CASE_BOTTOM = -35.2


def _scaled(points, s):
    return [(x * s, y * s) for x, y in points]


def _rot(points, a):
    c, s = math.cos(a), math.sin(a)
    return [(x * c - y * s, x * s + y * c) for x, y in points]


def _horn_pattern(centre, angle_deg):
    """The four horn screw positions around an axis, in the sketch plane of a part."""
    a = math.radians(angle_deg)
    return [(centre[0] + HORN_SCREW_R * math.cos(a + k * math.pi / 2),
             centre[1] + HORN_SCREW_R * math.sin(a + k * math.pi / 2)) for k in range(4)]


def _horn_plates(c, centre, y_in, y_out, angle_deg):
    """Bosses down to both horn faces, then axis hole and horn screws, on a pair of
    plates spanning +-(y_in..y_out) in Y (sketch coordinates are x, z)."""
    for y0 in (HORN_Y, -y_in):
        c.add('y', y0, [circ(*centre, HORN_BOSS_R)], y_in - HORN_Y, 'Boss down to the ST3215 horn face')
    for y0 in (HORN_Y, -y_out):
        c.cut('y', y0, [circ(*centre, AXIS_HOLE_R)], y_out - HORN_Y, 'Axis hole: idler bushing, horn screw access')
        c.cut('y', y0, [circ(x, z, M3_CLEAR) for x, z in _horn_pattern(centre, angle_deg)], y_out - HORN_Y,
              'M3 horn screws')
    for y0 in (y_out - HORN_COUNTERBORE, -y_out):
        c.cut('y', y0, [circ(x, z, M3_HEAD) for x, z in _horn_pattern(centre, angle_deg)], HORN_COUNTERBORE,
              'Button head counterbores')


def coxa(s=S, servo=True):
    g = lambda v: v * s  # noqa: E731
    c = Part('CoxaCarrier')
    c.add('z', g(4), [circ(0, 0, g(16))], g(4.8), 'Closed yaw cap')
    c.add('z', g(4), [poly(_scaled([(0, -16), (16, -14), (34, -20.8), (34, 20.8), (16, 14), (0, 16)], s))],
          g(2.4), 'Symmetric short proximal link')
    c.cut('z', g(4), [circ(0, 0, g(13.8))], g(3.2), 'Yaw output coupling reserve')
    hip = (g(45), g(-12))
    for side in (-1, 1):
        y = g(-16.1) if side < 0 else g(14.3)
        c.add('y', y, [cap((g(34), g(5)), hip, g(4.8))], g(1.8), 'Bilateral internal shoulder support')
        c.add('y', y, [circ(*hip, g(11.2))], g(1.8), 'Shoulder pivot plate inside upper enclosure')
        if not servo:
            c.cut('y', y, [circ(*hip, 3.2)], g(1.8), 'Provisional axis/tool access hidden by red upper cover')
    if servo:
        top = g(4) + g(4.8)
        c.add('z', YAW_HORN_Z, [circ(0, 0, 11.0)], g(4) + g(3.2) - YAW_HORN_Z, 'Hub down to the yaw servo horn')
        c.cut('z', YAW_HORN_Z, [circ(x, y, M3_CLEAR) for x, y in _horn_pattern((0, 0), 0)], top - YAW_HORN_Z,
              'M3 yaw horn screws')
        c.cut('z', top - 3.2, [circ(x, y, M3_HEAD) for x, y in _horn_pattern((0, 0), 0)], 3.2,
              'Socket head counterbores')
        c.cut('z', YAW_HORN_Z, [circ(0, 0, AXIS_HOLE_R)], 1.2, 'Relief for the horn centre screw')
        # The hip servo case rides on the femur, its horns on these plates: horn screws
        # line up with the femur axes in the modelled pose (femur pitched FEMUR_ANGLE).
        _horn_plates(c, hip, g(14.3), g(16.1), layout.FEMUR_ANGLE)
    return c


def _slot(c, s, side, x0, z0, x1, z1):
    y = 14.0 * s if side > 0 else -16.5 * s
    c.cut('y', y, [rect(x0 * s, z0 * s, x1 * s, z1 * s)], 2.5 * s, 'Clevis slot')


# Femur, servo version: cover screw and tongue over / in front of the servo cases.
SCREW_X, SCREW_Z = 26.0 * S, 14.0            # x is the concept's, between the two cases
TONGUE = (22.8 * S, 29.2 * S, 17.0, 11.1, 16.9)   # x0, x1, y0 (tip), z0, z1
BRIDGE_X = (SCREW_X - 7.0, SCREW_X + 7.0)
BRIDGE_Z = 12.5                              # case faces at +-12.36: the bridges clamp the long ends


def femur_standoffs():
    """Case screws used in the femur (femur frame x, z). The knee servo's lower one is
    left out: the tibia's rear fork plate sweeps over that spot when the knee folds."""
    hip, knee = CASE_SCREW[0], layout.FEMUR - CASE_SCREW[0]
    return ((hip, -CASE_SCREW[1]), (hip, CASE_SCREW[1]), (knee, CASE_SCREW[1]))


def femur(s=S, servo=True):
    g = lambda v: v * s  # noqa: E731
    c = Part('FemurCarrier')
    c.add('y', g(-18.7), [cap((0, 0), (g(52), 0), g(14))], g(35.3), 'One continuous upper arm outer skin')
    c.cut('y', g(-16.9), [cap((0, 0), (g(52), 0), g(12.2))], g(33.5), 'Two-actuator interior open at front')
    for side in (-1, 1):
        _slot(c, s, side, -6, 9, 22, 26)
        _slot(c, s, side, 18, -30, 66, -7)
    if not servo:
        c.add('z', 4.0, [rect(22.2, -17.4, 29.8, 16.6)], 8.0, 'Upper central retention bridge in actuator gap')
        c.cut('z', 4.7, [rect(22.4, 10, 29.6, 16.6)], 6.8, 'Keyed cover tongue pocket')
        c.cut('y', -18.7, [circ(26, 8.1, 1.7)], 28.9, 'Single central rear service screw path')
        c.cut('y', -18.7, [circ(26, 8.1, 3.1)], 1.8, 'Flush rear screw head recess')
        return c
    rear, front, roof = g(-18.7), g(16.6), g(12.2)
    x0, x1 = BRIDGE_X
    c.add('z', BRIDGE_Z, [rect(x0, g(-17.4), x1, front)], g(14) - BRIDGE_Z, 'Retention bridge above the servo cases')
    c.add('z', -g(14), [rect(x0, -16.5, x1, 16.5)], g(14) - BRIDGE_Z, 'Lower bridge under the servo cases')
    c.cut('z', TONGUE[3] - 0.2, [rect(g(22.4), TONGUE[2] - 0.2, g(29.6), front)], roof - TONGUE[3] + 0.2,
          'Keyed cover tongue pocket')
    # M2 standoffs from the rear wall to the case bottom face
    bottom = HORN_Y + CASE_BOTTOM
    for x, z in femur_standoffs():
        c.add('y', g(-16.9), [circ(x, z, 2.2)], bottom - g(-16.9), 'M2 standoff to the servo case')
        c.cut('y', rear, [circ(x, z, M2_CLEAR)], bottom - rear, 'M2 case screw')
        c.cut('y', rear, [circ(x, z, M2_HEAD)], 1.4, 'M2 head recess')
    c.cut('y', rear, [circ(SCREW_X, SCREW_Z, M3_CLEAR)], TONGUE[2] - rear, 'Rear cover screw path over the servos')
    c.cut('y', rear, [circ(SCREW_X, SCREW_Z, 2.9)], 3.2, 'Rear screw head recess')
    return c


def cheek(s=S, servo=True):
    g = lambda v: v * s  # noqa: E731
    c = Part('FemurCheek')
    c.add('y', g(16.9), [cap((0, 0), (g(52), 0), g(14))], g(1.8), 'Closed front panel hides both servo bodies')
    if not servo:
        c.add('z', 5.0, [rect(22.8, 10.2, 29.2, 17.0)], 6.2, 'Single keyed internal retention tongue')
        c.cut('y', 10.2, [circ(26, 8.1, 2.1)], 4.2, 'Provisional M3 insert cavity')
        return c
    x0, x1, y0, z0, z1 = TONGUE
    c.add('z', z0, [rect(x0, y0, x1, g(16.9) + 0.2)], z1 - z0, 'Keyed retention tongue in front of the servos')
    c.cut('y', y0, [circ(SCREW_X, SCREW_Z, M3_INSERT)], 5.5, 'M3 heat-set insert')
    return c


def tibia(s=S, servo=True):
    g = lambda v: v * s  # noqa: E731
    c = Part('Tibia')
    c.add('y', g(14.3), [circ(0, 0, g(11.2))], g(1.8), 'Internal forward knee pivot plate')
    outline = poly(_scaled([(0, -10), (14, -9), (28, -7.5), (40, -6.5), (40, 6.5), (28, 7.5), (14, 9), (0, 10)], s))
    c.add('y', g(14.3), [outline], g(1.8), 'Forward inner fork leg')
    c.loft('x', [(g(38), roundrect(g(-16.1), g(-6.5), g(16.1), g(6.5), g(1.2))),
                 (g(48), roundrect(g(-4), g(-5.5), g(4), g(5.5), g(1.2)))], note='Transition into the beam')
    c.add('y', g(-16.1), [outline], g(1.8), 'Rear inner fork leg linked by transition')
    c.add('y', g(-16.1), [circ(0, 0, g(11.2))], g(1.8), 'Internal rear knee pivot plate')
    c.loft('x', [(g(48), roundrect(g(-4), g(-5.5), g(4), g(5.5), g(1.2))),
                 (g(93), roundrect(g(-3.4), g(-2.3), g(3.4), g(2.3), g(1.0)))], note='Slim tapered centred beam')
    if not servo:
        for y in (g(-16.1), g(14.3)):
            c.cut('y', y, [circ(0, 0, 3.2)], g(1.8), 'Knee axis/tool access concealed by the cover')
        return c
    # knee horn screws line up with the femur axes in the modelled pose
    _horn_plates(c, (0, 0), g(14.3), g(16.1), layout.FEMUR_ANGLE - layout.TIBIA_ANGLE)
    return c


def foot(s=S, servo=True):
    g = lambda v: v * s  # noqa: E731
    c = Part('FootPad')
    c.add('y', g(-5.5), [circ(g(93), 0, g(5.5))], g(11), 'Symmetric compliant toe')
    c.cut('y', g(-4.6), [roundrect(g(87), g(-3.2), g(94.3), g(3.2), g(.8))], g(9.2), 'Centred toe socket')
    return c


# ------------------------------------------------------------------ core
def cassette_fasteners(servo=True):
    if not servo:
        return ((21., 16.), (-21., -16.))
    return ((0.0, 26.4 * S), (0.0, -26.4 * S))     # same radius, turned clear of the yaw servos


def yaw_standoffs():
    """Floor standoffs of the yaw servos, robot frame: the two pairs of case screw holes."""
    out = []
    for i in range(layout.LEGS):
        a = math.radians(layout.leg_angle(i))
        for xs in (8.3, CASE_SCREW[0]):
            for ys in (-CASE_SCREW[1], CASE_SCREW[1]):
                r = layout.YAW_RADIUS - xs      # the servo's long end points at the centre
                out.append((r * math.cos(a) - ys * math.sin(a), r * math.sin(a) + ys * math.cos(a)))
    return out


YAW_CASE_BOTTOM = YAW_HORN_Z + CASE_BOTTOM      # -33.7


def tub(s=S, servo=True):
    g = lambda v: v * s  # noqa: E731
    c = Part('CoreTub')
    bottom, floor = g(-32), g(-29)
    c.add('z', bottom, [poly(_scaled(rounded_hex(), s))], -bottom, 'Continuous structural body')
    c.cut('z', floor, [poly(_scaled(rounded_hex(4.2), s))], -floor, 'Hollow core, floor and walls')
    recess = 3.2 if servo else 2
    for x, y in _scaled(lid_fasteners(), s):
        c.add('z', floor, [circ(x, y, g(4.2))], -floor, 'Integral concealed lid screw column')
        c.cut('z', bottom, [circ(x, y, M3_CLEAR)], -bottom, 'Underside M3 clearance shaft')
        c.cut('z', bottom, [circ(x, y, M3_HEAD)], recess, 'Recessed underside screw head')
        c.add('z', g(-5), [circ(x, y, g(6.5))], g(5), 'Integral wide insert seating collar')
        c.cut('z', g(-5), [circ(x, y, M3_CLEAR)], g(5), 'Keep screw shaft open through widened collar')
        c.cut('z', g(-4), [circ(x, y, g(5.3))], g(4), 'Lid boss receiving pocket with radial clearance')
    for x, y in cassette_fasteners(servo):
        c.add('z', floor, [circ(x, y, g(3.5))], g(14), 'Integral cassette support column')
        top = floor + g(14)
        depth = 5.7 if servo else 5
        c.cut('z', top - depth, [circ(x, y, M3_INSERT)], depth, 'M3 insert cavity, cassette')
    for x in (g(-23.3), g(23.3)):
        c.add('z', floor, [rect(x - g(.7), g(-9), x + g(.7), g(9))], g(2), 'Battery side guide, foam allowance')
    for y in (g(-13.), g(13.)):
        c.add('z', floor, [rect(g(-21.8), y - g(.7), g(21.8), y + g(.7))], g(2), 'Battery end guide')
    floor_t = floor - bottom
    if servo:
        c.cut('z', bottom, [cap((g(-8), y), (g(8), y), g(1.3)) for y in (-21.2, 21.2)], floor_t,
              'Battery soft strap routing, across the pack')
    else:
        c.cut('z', bottom, [cap((x, -8), (x, 8), 1.3) for x in (-24., 24.)], 3, 'Battery soft strap routing')
    for angle in (30, 90, 150, 210, 270, 330):
        rad = math.radians(angle)
        a = (g(35) * math.cos(rad), g(35) * math.sin(rad))
        b = (g(43) * math.cos(rad), g(43) * math.sin(rad))
        c.cut('z', bottom, [cap(a, b, g(1.1))], floor_t, 'Discreet underside ventilation slot')
    for angle in (30, 90, 150, 210, 270, 330):
        pts = _rot(_scaled([(30, -7), (53, -10), (58, 0), (53, 10), (30, 7)], s), math.radians(angle))
        c.cut('z', bottom, [poly(pts)], floor_t, 'Underside weight relief between actuator bays')
    if servo:
        spots = yaw_standoffs()
        c.add('z', floor, [circ(x, y, 2.2) for x, y in spots], YAW_CASE_BOTTOM - floor, 'M2 yaw servo standoffs')
        c.cut('z', bottom, [circ(x, y, M2_CLEAR) for x, y in spots], YAW_CASE_BOTTOM - bottom, 'M2 case screws')
        c.cut('z', bottom, [circ(x, y, M2_HEAD) for x, y in spots], 1.5, 'M2 head recesses')
    return c


def lid(s=S, servo=True):
    g = lambda v: v * s  # noqa: E731
    c = Part('CoreLid')
    c.add('z', g(.5), [poly(_scaled(rounded_hex(), s))], g(2), 'Low peripheral top skin')
    c.add('z', g(2.5), [circ(0, 0, g(31.6))], g(7.9), 'Compact central enclosure island')
    c.loft('z', [(g(10.4), circ(0, 0, g(31.6))), (g(12.4), circ(0, 0, g(30.6)))], note='Soft crown edge')
    c.cut('z', g(.5), [circ(0, 0, g(29.2))], g(9.5), 'Open underside cavity')
    for index in range(6):
        angle = index * math.pi / 3
        x, y = g(49) * math.cos(angle), g(49) * math.sin(angle)
        c.cut('z', g(.5), [circ(x, y, g(16.8))], g(2), 'Yaw rotating hub peripheral clearance')
    for x, y in _scaled(lid_fasteners(), s):
        c.add('z', g(-4), [circ(x, y, g(5))], g(4.5), 'Concealed integral lid insert boss')
        c.cut('z', g(-4), [circ(x, y, M3_INSERT)], 6.0 if servo else 4.3, 'M3 insert cavity')
    return c


def cassette(s=S, servo=True):
    g = lambda v: v * s  # noqa: E731
    c = Part('ElectronicsCassette')
    z0 = g(-15)
    c.add('z', z0, [circ(0, 0, g(28.8))], g(2), 'Low removable electronics carrier')
    bay = ((33.0, -12.9), (62.0, -12.9), (62.0, 12.9), (33.0, 12.9)) if servo else \
        ((26.6, -6.9), (59.4, -6.9), (59.4, 6.9), (26.6, 6.9))
    for index in range(6):
        c.cut('z', z0, [poly(_rot(bay, index * math.pi / 3))], g(2), 'Yaw servo bay clearance')
    for x, y in cassette_fasteners(servo):
        c.cut('z', z0, [circ(x, y, M3_CLEAR)], g(2), 'Hidden carrier fastener path')
    top = z0 + g(2)
    if servo:
        regulator = [(x, y) for x in (-19, 19) for y in (-19, 19)]
        posts = [(x, y) for x in (-27.5, 27.5) for y in (-6, 6)]
        harness = [cap((-9.8, y), (9.8, y), 1.68) for y in (-30.5, 30.5)]
    else:
        a = math.pi / 6
        regulator = [(x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a))
                     for x in (-15, 15) for y in (-20, 20)]
        posts = [(x, y) for x in (-25, 25) for y in (-4, 4)]
        harness = [cap((-7, y), (7, y), 1.2) for y in (-25, 25)]
    for x, y in regulator:
        c.add('z', top, [circ(x, y, g(2))], g(1), 'Regulator insulating support')
    for x, y in posts:
        c.add('z', top, [rect(x - g(.8), y - g(.8), x + g(.8), y + g(.8))], -top, 'Controller support post')
    c.cut('z', z0, harness, g(2), 'Reserved harness route at carrier edge')
    return c


PRINTS = dict(CoreTub=tub, CoreLid=lid, ElectronicsCassette=cassette, CoxaCarrier=coxa,
              FemurCarrier=femur, FemurCheek=cheek, Tibia=tibia, FootPad=foot)


def electronics_reserves(s=S, servo=True):
    """Keep-out boxes (key, width, depth, z0, height, angle). Battery and controller are
    the concept's, scaled; the regulator box shrinks to stay inside the yaw servos."""
    g = lambda v: v * s  # noqa: E731
    reg = (44.0, 44.0, g(-12), g(10), 0.0) if servo else (34., 44., -12., 10., 30.)
    return (('BatteryReserve', g(43.), g(23.), g(-29.), g(13.), 0.0),
            ('RegulatorReserve',) + reg,
            ('ESP32Reserve', g(52.), g(24.), 0.0, g(8.), 0.0))
