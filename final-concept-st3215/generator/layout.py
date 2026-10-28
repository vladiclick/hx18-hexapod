"""Dimensions and joint frames of the HX18 final concept, sized for the Waveshare ST3215.

The design is final-concept/Automation/HexapodV5 unchanged, scaled by S. S = 1.4 is
the smallest uniform scale at which the ST3215 fits every joint of the concept:

  - femur, hip axis to knee axis: two ST3215 cases (35.1 mm from the output axis
    to the long end) must fit back to back: 2 x 35.1 + gap <= 52 * S
  - femur capsule, inner radius 12.2 * S: the case corner next to the output axis
    (10.15 mm behind it, 12.36 mm off the centre line) is 16.0 mm from the axis
  - coxa plates, 14.3 * S apart from the centre: the horn faces are 18.6 mm out

Units are mm. Frames follow HexapodV5.matrix(): local X radial and pitched up by
the joint angle, Y tangential (the hip and knee axes), Z completes the frame.
"""
import math

import cadquery as cq
from OCP.gp import gp_Ax3, gp_Dir, gp_Pnt, gp_Trsf

S = 1.4

# final-concept/Automation/HexapodV5/v3_geometry.py DEFAULT
CONCEPT = dict(yaw_radius=49.0, coxa=45.0, femur=52.0, tibia=93.0, shoulder_z=-12.0,
               femur_angle=55.0, tibia_angle=-72.0)

YAW_RADIUS = CONCEPT['yaw_radius'] * S          # 68.6
COXA = CONCEPT['coxa'] * S                      # 63.0, yaw axis to hip axis
FEMUR = CONCEPT['femur'] * S                    # 72.8, hip axis to knee axis
TIBIA = CONCEPT['tibia'] * S                    # 130.2, knee axis to the toe centre
SHOULDER_Z = CONCEPT['shoulder_z'] * S          # -16.8
FEMUR_ANGLE = CONCEPT['femur_angle']            # 55 deg
TIBIA_ANGLE = CONCEPT['tibia_angle']            # -72 deg

LEGS = 6
# Joint limits tested for the concept (final-concept/Motion-validation.json), around the modelled pose.
RANGES = dict(yaw=(-20.0, 20.0), hip=(-12.0, 12.0), knee=(-15.0, 15.0))

# ST3215 placement. In the femur and coxa frames the servo axis is Y and the
# drive horn faces +Y (behind the red cover); the horn faces sit at +-HORN_Y.
HORN_Y = 18.625
YAW_HORN_Z = 1.5            # drive horn face of the yaw servo, coxa frame; its case top is at -0.6


def position(a, x, y, z):
    r = math.radians(a)
    return (math.cos(r) * x - math.sin(r) * y, math.sin(r) * x + math.cos(r) * y, z)


def location(yaw, pitch, origin):
    """HexapodV5.matrix(yaw, pitch, origin) as a cadquery Location."""
    a, b = map(math.radians, (yaw, pitch))
    x = (math.cos(a) * math.cos(b), math.sin(a) * math.cos(b), math.sin(b))
    z = (-math.cos(a) * math.sin(b), -math.sin(a) * math.sin(b), math.cos(b))
    t = gp_Trsf()
    t.SetTransformation(gp_Ax3(gp_Pnt(*origin), gp_Dir(*z), gp_Dir(*x)), gp_Ax3())
    return cq.Location(t)


def leg_angle(i):
    return 60.0 * i


def joints(i, yaw=0.0, hip=0.0, knee=0.0, s=S):
    """Yaw, hip and knee axis points of leg i (0-5) for joint offsets from the modelled pose."""
    a = leg_angle(i)
    yawpt = position(a, CONCEPT['yaw_radius'] * s, 0, 0)
    dx, dy, _ = position(a + yaw, CONCEPT['coxa'] * s, 0, 0)
    shoulder = (yawpt[0] + dx, yawpt[1] + dy, CONCEPT['shoulder_z'] * s)
    f = math.radians(FEMUR_ANGLE + hip)
    femur = CONCEPT['femur'] * s
    ux, uy, _ = position(a + yaw, femur * math.cos(f), 0, 0)
    knee_pt = (shoulder[0] + ux, shoulder[1] + uy, shoulder[2] + femur * math.sin(f))
    return yawpt, shoulder, knee_pt


def frames(i, yaw=0.0, hip=0.0, knee=0.0, s=S):
    """Link frames of leg i: base (fixed to the core, at the yaw axis), coxa, femur, tibia."""
    a = leg_angle(i)
    yawpt, shoulder, knee_pt = joints(i, yaw, hip, knee, s)
    return dict(base=location(a, 0, yawpt), coxa=location(a + yaw, 0, yawpt),
                femur=location(a + yaw, FEMUR_ANGLE + hip, shoulder),
                tibia=location(a + yaw, TIBIA_ANGLE + hip + knee, knee_pt))


def apply(loc, x=0.0, y=0.0, z=0.0):
    return cq.Vector(gp_Pnt(x, y, z).Transformed(loc.wrapped.Transformation()))


def foot_point(i, yaw=0.0, hip=0.0, knee=0.0, s=S):
    """Toe centre: (93, 0, 0) * s in the tibia frame, as in the concept."""
    return apply(frames(i, yaw, hip, knee, s)['tibia'], CONCEPT['tibia'] * s)


def rel(outer, inner):
    """inner expressed in the outer frame."""
    return outer.inverse * inner
