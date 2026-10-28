"""Dimensions and joint frames of HX18 built around 18 x Waveshare ST3215.

Leg frame: origin on the yaw axis in the yaw drive-horn face, x radially out,
y tangential (counter-clockwise), z up. Every leg is identical; leg i is the
leg frame turned by LEG_ANGLES[i] about the robot Z axis and moved out by R_YAW.

All three joints use the same pattern: the servo body is held by one link and
both horns (drive + idler) are bolted to the next link, so every joint is
supported on both sides.
"""
import math

import cadquery as cq
from OCP.gp import gp_Pnt, gp_Trsf

import servo

LEG_ANGLES = (30.0, 90.0, 150.0, 210.0, 270.0, 330.0)   # +X is the front, between legs 1 and 6
# Robot frame: +X front, +Y left. LEG_ANGLES go counter-clockwise from the front.
LEG_NAMES = ('front left', 'middle left', 'rear left', 'rear right', 'middle right', 'front right')

R_YAW = 80.0            # yaw axis distance from the body centre
PLATE = 4.0             # thickness of every bracket plate on a horn
HUB_R = 12.5            # bracket hub radius around a joint axis (horn is 19.2 mm)
HORN_FACE = -servo.IDLER_HORN_Z[0] / 2 + servo.DRIVE_HORN_Z[1] / 2   # 18.625: horn face to servo mid-plane
PLATE_OUT = HORN_FACE + PLATE                                         # 22.625: outside of bracket plates
CLEAR = 0.4             # fit clearance around servo cases

Z_MID = servo.MID_PLANE_Z            # -18.625: mid-plane of the yaw servo = hip axis height
L_COXA = 56.5           # yaw axis -> hip axis
L_FEMUR = 62.0          # hip axis -> knee axis
# The tibia runs straight down from the knee to a bend, then the shank turns inwards. The bend lets
# the foot reach under the body while the knee itself only needs to fold 30 degrees.
TIBIA_BEND_Z = -36.0    # bend point below the knee axis
TIBIA_BEND = 25.0       # shank angle towards the body, degrees
SHANK = 100.0           # bend point -> tip of the toe
TOE = (-SHANK * math.sin(math.radians(TIBIA_BEND)), 0.0,
       TIBIA_BEND_Z - SHANK * math.cos(math.radians(TIBIA_BEND)))   # toe tip in the tibia frame

# Stand pose used for the renders (degrees). Hip + lifts the femur, knee + swings the foot out.
# With hip 25 and knee 0 the shank stands vertical.
STAND = dict(yaw=0.0, hip=25.0, knee=0.0)
# Joint ranges proven free of collisions by checks.py.
RANGES = dict(yaw=(-40.0, 40.0), hip=(-30.0, 90.0), knee=(-30.0, 110.0))

# ---- servo placements inside their holding link -------------------------------------------
# Rotation that puts the servo frame (x along case, z out of the drive horn) into a link frame
# with the servo axis along link +y and the case body along link -x.
_AXIS_ALONG_Y = ((-1, 0, 0), (0, 0, 1), (0, 1, 0))


def _loc(rows, x=0.0, y=0.0, z=0.0):
    t = gp_Trsf()
    t.SetValues(*rows[0], x, *rows[1], y, *rows[2], z)
    return cq.Location(t)


def _rot_z(deg):
    return cq.Location(cq.Vector(), cq.Vector(0, 0, 1), deg)


def _rot_y(deg):
    return cq.Location(cq.Vector(), cq.Vector(0, 1, 0), deg)


def _move(x=0.0, y=0.0, z=0.0):
    return cq.Location(cq.Vector(x, y, z))


YAW_SERVO = _rot_z(180)                                         # in the leg frame: body points inward
HIP_SERVO = _loc(_AXIS_ALONG_Y, L_COXA, HORN_FACE, Z_MID)       # in the coxa frame
KNEE_SERVO = _loc(_AXIS_ALONG_Y, L_FEMUR, HORN_FACE, 0.0)       # in the femur frame


def leg_base(i):
    return _rot_z(LEG_ANGLES[i]) * _move(R_YAW)


def frames(i, yaw=0.0, hip=0.0, knee=0.0):
    """World locations of the leg, coxa, femur and tibia frames of leg i."""
    leg = leg_base(i)
    coxa = leg * _rot_z(yaw)
    femur = coxa * _move(L_COXA, 0, Z_MID) * _rot_y(-hip)
    tibia = femur * _move(L_FEMUR) * _rot_y(-knee)
    return dict(leg=leg, coxa=coxa, femur=femur, tibia=tibia)


def apply(loc, x=0.0, y=0.0, z=0.0):
    """A point given in the frame `loc`, in world coordinates."""
    q = gp_Pnt(x, y, z).Transformed(loc.wrapped.Transformation())
    return cq.Vector(q.X(), q.Y(), q.Z())


def foot_point(i, yaw=0.0, hip=0.0, knee=0.0):
    return apply(frames(i, yaw, hip, knee)['tibia'], *TOE)


def stand_height():
    """Height of the leg frame origin above the ground in the stand pose."""
    return -foot_point(0, **STAND).z


def leg_ik(x, y, z):
    """Joint angles (yaw, hip, knee in degrees) that put the toe of a leg at (x, y, z) in its leg frame."""
    yaw = math.atan2(y, x)
    r = math.hypot(x, y) - L_COXA
    h = z - Z_MID
    lt = math.hypot(TOE[0], TOE[2])
    phi0 = math.atan2(TOE[2], TOE[0])            # toe direction in the tibia frame at knee = 0
    d = math.hypot(r, h)
    if not abs(L_FEMUR - lt) <= d <= L_FEMUR + lt:
        raise ValueError(f'toe target out of reach: {x:.1f}, {y:.1f}, {z:.1f}')
    inner = math.acos((L_FEMUR ** 2 + lt ** 2 - d ** 2) / (2 * L_FEMUR * lt))   # angle at the knee
    alpha = math.acos((L_FEMUR ** 2 + d ** 2 - lt ** 2) / (2 * L_FEMUR * d))    # femur above the hip-toe line
    hip = math.atan2(h, r) + alpha
    knee = -(math.pi - inner) - phi0
    return math.degrees(yaw), math.degrees(hip), math.degrees(knee)


def toe_in_leg_frame(yaw=0.0, hip=0.0, knee=0.0):
    p = apply(frames(0, yaw, hip, knee)['tibia'], *TOE)
    return apply(leg_base(0).inverse, p.x, p.y, p.z)
