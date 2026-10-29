"""Tripod gait: three feet stay planted on the ground while they carry the body.

Legs 1, 3, 5 and 2, 4, 6 alternate. The body moves at constant speed; a swinging
foot eases off the ground and back down (zero speed against the ground at lift-off
and touch-down), so no foot slides.
"""
import math

import layout


def ik(i, foot):
    """Joint offsets (yaw, hip, knee) from the modelled pose that put the toe centre of
    leg i at `foot` (x, y, z in the body frame)."""
    yx, yy, _ = layout.position(layout.leg_angle(i), layout.YAW_RADIUS, 0, 0)
    dx, dy = foot[0] - yx, foot[1] - yy
    yaw = math.degrees(math.atan2(dy, dx)) - layout.leg_angle(i)
    yaw = (yaw + 180) % 360 - 180
    u = math.hypot(dx, dy) - layout.COXA
    w = foot[2] - layout.SHOULDER_Z
    l1, l2 = layout.FEMUR, layout.TIBIA
    c = (u * u + w * w - l1 * l1 - l2 * l2) / (2 * l1 * l2)
    if abs(c) > 1:
        raise ValueError(f'leg {i + 1}: foot out of reach')
    phi = math.acos(c)                                   # femur-to-tibia angle, 127 deg in the modelled pose
    theta1 = math.atan2(w, u) + math.atan2(l2 * math.sin(phi), l1 + l2 * math.cos(phi))
    hip = math.degrees(theta1) - layout.FEMUR_ANGLE
    knee = layout.FEMUR_ANGLE - layout.TIBIA_ANGLE - math.degrees(phi)
    return yaw, hip, knee


def tripod(frames=40, stride=50.0, lift=32.0, heading=90.0):
    """One gait cycle. Returns [(body offset (x, y), [(yaw, hip, knee)] * 6)].

    stride: body travel while a foot is planted; the body moves 2 * stride per cycle."""
    hx, hy = math.cos(math.radians(heading)), math.sin(math.radians(heading))
    home = [layout.foot_point(i) for i in range(layout.LEGS)]
    out = []
    for n in range(frames):
        t = n / frames
        poses = []
        for i in range(layout.LEGS):
            tau = (t - (0.5 if i % 2 else 0.0)) % 1.0
            if tau < 0.5:                                 # planted
                along, up = stride / 2 - stride * tau / 0.5, 0.0
            else:                                         # swing, eased against the ground
                q = (tau - 0.5) / 0.5
                along = -stride / 2 + stride * (1 - math.cos(math.pi * q)) - stride * q
                up = lift * math.sin(math.pi * q) ** 2
            p = home[i]
            poses.append(ik(i, (p.x + hx * along, p.y + hy * along, p.z + up)))
        out.append(((hx * 2 * stride * t, hy * 2 * stride * t), poses))
    return out
