"""Tripod gait used for the walking animation: three legs swing while the other three push."""
import math

import layout

TRIPODS = ((0, 2, 4), (1, 3, 5))


def tripod(frames=24, stride=50.0, lift=28.0):
    """Joint angles of all six legs for each frame of one gait cycle (body fixed, walking towards +X)."""
    home = layout.toe_in_leg_frame(**layout.STAND)
    cycle = []
    for f in range(frames):
        phase = f / frames
        poses = []
        for i, angle in enumerate(layout.LEG_ANGLES):
            p = (phase + (0.0 if i in TRIPODS[0] else 0.5)) % 1.0
            if p < 0.5:                      # swing: toe moves forward through the air
                t = p / 0.5
                dx, dz = stride * (t - 0.5), lift * math.sin(math.pi * t)
            else:                            # stance: toe pushes back on the ground
                t = (p - 0.5) / 0.5
                dx, dz = stride * (0.5 - t), 0.0
            a = math.radians(angle)          # robot +X expressed in this leg's frame
            poses.append(layout.leg_ik(home.x + dx * math.cos(a), home.y - dx * math.sin(a), home.z + dz))
        cycle.append(poses)
    return cycle
