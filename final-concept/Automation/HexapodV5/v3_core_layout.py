"""Concept core envelope in millimetres, not a selected electronic BOM.

Actuator bodies/ears/connectors remain unverified until a model is selected.
The checks here compare reserved boxes, never measured manufactured parts.
"""
import math


def lid_fasteners():
    return tuple((60*math.cos(math.radians(a)), 60*math.sin(math.radians(a)))
                 for a in (30, 150, 210, 330))


def cassette_fasteners():
    return ((21., 16.), (-21., -16.))


def core_dimensions():
    return dict(outer_radius=72., tub_bottom=-32., floor_top=-29., tub_top=0.,
                wall=1.8, rim_bottom=.5, rim_top=2.5, island_radius=31.6,
                island_inner_radius=29.2, island_top=12.4, cassette_radius=28.8)


def electronics_reserves():
    status = 'reserved envelope; component not selected'
    return tuple(dict(key=k, width=w, depth=d, z=z, height=h, angle=30. if k=='RegulatorReserve' else 0., status=status)
                 for k, w, d, z, h in (
                     ('BatteryReserve', 43., 23., -29., 13.),
                     ('RegulatorReserve', 34., 44., -12., 10.),
                     ('ESP32Reserve', 52., 24., 0., 8.)))


def yaw_case_distance(point, index):
    """XY distance to the generic yaw reserve, x27..59,y+/-6.5.

    Above Z0 the actual rotating hub is a different circular reserve.
    """
    angle = index*math.pi/3
    x, y = point
    radial = x*math.cos(angle)+y*math.sin(angle)
    tangent = -x*math.sin(angle)+y*math.cos(angle)
    dx = max(27-radial, 0., radial-59)
    dy = max(abs(tangent)-6.5, 0.)
    return math.hypot(dx, dy)


def island_clearance(reserve):
    return 29.2-math.hypot(reserve['width']/2, reserve['depth']/2)

def rounded_hex(corner_radius=6.0, vertex_radius=66.0):
    return tuple((vertex_radius*math.cos(i*math.pi/3)+corner_radius*math.cos(i*math.pi/3-math.pi/6+j*math.pi/24),vertex_radius*math.sin(i*math.pi/3)+corner_radius*math.sin(i*math.pi/3-math.pi/6+j*math.pi/24)) for i in range(6) for j in range(9))
