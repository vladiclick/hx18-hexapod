"""Pure layout numbers for the V5 closed inline leg concept.

The values here describe geometric envelopes for the Fusion builder and tests.
They are not validation that a specific actuator body can be installed or that
any particular manufacturing process is ready for production.
"""
from __future__ import annotations

import math
from typing import Sequence, Tuple

Point3 = Tuple[float, float, float]
Box = Tuple[Point3, Point3]

_FEMUR_LENGTH = 52.0
_FEMUR_NEUTRAL_DEG = 55.0
_TIBIA_LENGTH = 93.0
_TIBIA_ABS_DEG = -72.0
_FOOT_LATERAL = 0.0

_OUTER_CAPSULE_START = (0.0, 0.0)
_OUTER_CAPSULE_END = (_FEMUR_LENGTH, 0.0)
_OUTER_CAPSULE_RADIUS = 14.0
_INTERNAL_RADIUS = 12.2
_SHELL_Y_HALF = 18.7
_INNER_CAVITY_Y_HALF = 16.9

_CASE_Y_HALF = 13.5
_HIP_CASE: Box = ((-10.0, -_CASE_Y_HALF, -6.5), (22.0, _CASE_Y_HALF, 6.5))
_KNEE_CASE: Box = ((30.0, -_CASE_Y_HALF, -6.5), (62.0, _CASE_Y_HALF, 6.5))
_CASES = (_HIP_CASE, _KNEE_CASE)

_YOKE_PLATE_INNER_Y = 14.3
_YOKE_PLATE_OUTER_Y = 16.1
_YOKE_PLATE_THICKNESS = _YOKE_PLATE_OUTER_Y - _YOKE_PLATE_INNER_Y
_YOKE_CAP_RADIUS = 11.2
_YOKE_CASE_GAP = _YOKE_PLATE_INNER_Y - _CASE_Y_HALF
_YOKE_SKIN_GAP = _INNER_CAVITY_Y_HALF - _YOKE_PLATE_OUTER_Y
_YOKE_RADIAL_GAP = _INTERNAL_RADIUS - _YOKE_CAP_RADIUS
_YOKE_PLATES = (
    ((-10.0, -_YOKE_PLATE_OUTER_Y, -_YOKE_CAP_RADIUS), (62.0, -_YOKE_PLATE_INNER_Y, _YOKE_CAP_RADIUS)),
    ((-10.0, _YOKE_PLATE_INNER_Y, -_YOKE_CAP_RADIUS), (62.0, _YOKE_PLATE_OUTER_Y, _YOKE_CAP_RADIUS)),
)

_BRIDGE_X_MIN = 22.2
_BRIDGE_X_MAX = 29.8
_BRIDGE_X_CENTER = 26.0
_BRIDGE_Y_MIN = -17.4
_BRIDGE_Y_MAX = 16.6
_BRIDGE_Z_MIN = 4.0
_BRIDGE_Z_MAX = 12.0
_RETENTION_POCKET_Z = (4.7, 11.5)
_RED_TONGUE_Z = (5.0, 11.2)
_M3_INSERT_CENTER_Z = 8.1
_M3_INSERT_RADIUS = 2.1

_TRANSITION_START_X = 38.0
_TRANSITION_START_Y_HALF = _YOKE_PLATE_OUTER_Y
_TRANSITION_START_Z_HALF = 6.5
_TRANSITION_TAPER_X = 48.0
_TRANSITION_TAPER_Y_HALF = 4.0
_TRANSITION_TAPER_Z_HALF = 5.5
_BLADE_END_X = 93.0
_BLADE_END_Y_HALF = 3.4
_BLADE_END_Z_HALF = 2.3

_RED_FORECOVER_Y_MIN = 16.9
_RED_FORECOVER_Y_MAX = 18.7
_CARRIER_Y_MIN = -18.7
_CARRIER_Y_MAX = 16.6

_COXA_FORK_SLOT_X = (-6.0, 22.0)
_COXA_FORK_SLOT_Z = (9.0, 26.0)
_KNEE_FORK_SLOT_X = (18.0, 66.0)
_KNEE_FORK_SLOT_Z = (-30.0, -7.0)
_FORK_SLOT_Y_INNER = 14.0
_FORK_SLOT_Y_OUTER = 16.5

_FORECAP_SCREW_X = 26.0
_FORECAP_SCREW_Z = 8.1
_FORECAP_SCREW_Y_START = -16.9
_FORECAP_SCREW_Y_END = 13.1
_FORECAP_SCREW_LENGTH = _FORECAP_SCREW_Y_END - _FORECAP_SCREW_Y_START
_FORECAP_TONGUE_Y = (10.2, 17.0)
_FORECAP_TONGUE_Z = _RED_TONGUE_Z

_FEMUR_SHELL_Z_HALF = 14.0
_RELATIVE_BASE_DEG = -127.0
_CLEARANCE_SAMPLE_X = _TRANSITION_START_X
_CLEARANCE_SAMPLE_Z_HALF = _TRANSITION_START_Z_HALF
_SERVICE_NOTE = "Physical servo-body replacement requires unbolting the joint axes; this layout only reserves envelopes."


def _is_finite_number(value: object) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(float(value))


def _point3(value: object, name: str) -> Point3:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)) or len(value) != 3:
        raise ValueError(f"{name} must be a 3D point")
    if not all(_is_finite_number(v) for v in value):
        raise ValueError(f"{name} must contain only finite numbers")
    return (float(value[0]), float(value[1]), float(value[2]))


def _box(lo: object, hi: object) -> Box:
    low = _point3(lo, "lo")
    high = _point3(hi, "hi")
    if not all(low[i] < high[i] for i in range(3)):
        raise ValueError("lo must be strictly below hi on every axis")
    return low, high


def _x_half_height_in_outer_capsule(x: float) -> float:
    if 0.0 <= x <= _FEMUR_LENGTH:
        return _OUTER_CAPSULE_RADIUS
    dx = -x if x < 0.0 else x - _FEMUR_LENGTH
    if dx > _OUTER_CAPSULE_RADIUS:
        return -1.0
    return math.sqrt(_OUTER_CAPSULE_RADIUS * _OUTER_CAPSULE_RADIUS - dx * dx)


def _paired_y_boxes(x_range: tuple[float, float], z_range: tuple[float, float]) -> list[Box]:
    return [
        ((x_range[0], -_FORK_SLOT_Y_OUTER, z_range[0]), (x_range[1], -_FORK_SLOT_Y_INNER, z_range[1])),
        ((x_range[0], _FORK_SLOT_Y_INNER, z_range[0]), (x_range[1], _FORK_SLOT_Y_OUTER, z_range[1])),
    ]


def case_fits(lo: object, hi: object) -> bool:
    """Return whether an actuator-placeholder box fits the reserved femur pod.

    This is an envelope check only: finite ordered bounds, centered lateral
    volume inside the internal cavity, and both x-end slices inside the outer
    capsule's available z height.
    """
    low, high = _box(lo, hi)
    if abs((low[1] + high[1]) * 0.5) > 1e-9:
        return False
    if max(abs(low[1]), abs(high[1])) > _INNER_CAVITY_Y_HALF:
        return False
    for x in (low[0], high[0]):
        z_limit = _x_half_height_in_outer_capsule(x)
        if z_limit < 0.0 or max(abs(low[2]), abs(high[2])) > z_limit:
            return False
    return True


def transition_clearance(knee: object) -> float:
    """Minimum vertical clearance from lower transition to the femur shell.

    `knee` is the relative knee offset in degrees around the nominal V5 folded
    pose.  The formula intentionally remains the simple envelope check against
    shell radius 14 mm.
    """
    if not _is_finite_number(knee):
        raise ValueError("knee must be a finite angle in degrees")
    theta = math.radians(_RELATIVE_BASE_DEG + float(knee))
    nearest_z = _CLEARANCE_SAMPLE_X * math.sin(theta) + _CLEARANCE_SAMPLE_Z_HALF * abs(math.cos(theta))
    return abs(nearest_z) - _FEMUR_SHELL_Z_HALF


def _named_box(name: str, lo: Point3, hi: Point3):
    return (name, lo, hi)


def layout() -> dict:
    """Return the deterministic V5 inline closed-arm envelope."""
    femur_shell = ((-14.0, -_SHELL_Y_HALF, -_FEMUR_SHELL_Z_HALF), (66.0, _SHELL_Y_HALF, _FEMUR_SHELL_Z_HALF))
    tibia_blade = ((_TRANSITION_START_X, -_TRANSITION_START_Y_HALF, -_TRANSITION_START_Z_HALF), (_BLADE_END_X, _TRANSITION_START_Y_HALF, _TRANSITION_START_Z_HALF))
    yoke_combined = ((-10.0, -_YOKE_PLATE_OUTER_Y, -_YOKE_CAP_RADIUS), (62.0, _YOKE_PLATE_OUTER_Y, _YOKE_CAP_RADIUS))
    foot = ((_BLADE_END_X - 8.0, -_BLADE_END_Y_HALF, -_BLADE_END_Z_HALF), (_BLADE_END_X + 8.0, _BLADE_END_Y_HALF, _BLADE_END_Z_HALF))
    bridge = ((_BRIDGE_X_MIN, _BRIDGE_Y_MIN, _BRIDGE_Z_MIN), (_BRIDGE_X_MAX, _BRIDGE_Y_MAX, _BRIDGE_Z_MAX))
    carrier_with_cover = ((-14.0, -_SHELL_Y_HALF, -_FEMUR_SHELL_Z_HALF), (66.0, _SHELL_Y_HALF, _FEMUR_SHELL_Z_HALF))

    centred_envelopes = [
        _named_box("FemurShell", *femur_shell),
        _named_box("TibiaBlade", *tibia_blade),
        _named_box("YokePlatesCombined", *yoke_combined),
        _named_box("Foot", *foot),
        _named_box("HipCase", *_HIP_CASE),
        _named_box("KneeCase", *_KNEE_CASE),
        _named_box("CarrierAndForecoverCombined", *carrier_with_cover),
    ]

    return {
        "femur_length": _FEMUR_LENGTH,
        "femur_neutral_deg": _FEMUR_NEUTRAL_DEG,
        "tibia_length": _TIBIA_LENGTH,
        "tibia_abs_deg": _TIBIA_ABS_DEG,
        "foot_lateral": _FOOT_LATERAL,
        "outer_capsule_start": _OUTER_CAPSULE_START,
        "outer_capsule_end": _OUTER_CAPSULE_END,
        "outer_capsule_radius": _OUTER_CAPSULE_RADIUS,
        "outer_capsule": (_OUTER_CAPSULE_START, _OUTER_CAPSULE_END, _OUTER_CAPSULE_RADIUS),
        "internal_radius": _INTERNAL_RADIUS,
        "shell_capsule_radius": _OUTER_CAPSULE_RADIUS,
        "shell_y_half": _SHELL_Y_HALF,
        "shell_half_width": _SHELL_Y_HALF,
        "inner_cavity_y_half": _INNER_CAVITY_Y_HALF,
        "case_y_half": _CASE_Y_HALF,
        "cases": list(_CASES),
        "hip_case": _HIP_CASE,
        "knee_case": _KNEE_CASE,
        "yoke_plate_inner_y": _YOKE_PLATE_INNER_Y,
        "yoke_plate_outer_y": _YOKE_PLATE_OUTER_Y,
        "yoke_plate_thickness": _YOKE_PLATE_THICKNESS,
        "yoke_inner": _YOKE_PLATE_INNER_Y,
        "yoke_outside": _YOKE_PLATE_OUTER_Y,
        "yoke_cap_radius": _YOKE_CAP_RADIUS,
        "yoke_case_gap": _YOKE_CASE_GAP,
        "yoke_skin_gap": _YOKE_SKIN_GAP,
        "yoke_radial_gap": _YOKE_RADIAL_GAP,
        "yoke_plates": list(_YOKE_PLATES),
        "bridge_x_min": _BRIDGE_X_MIN,
        "bridge_x_max": _BRIDGE_X_MAX,
        "bridge_x_center": _BRIDGE_X_CENTER,
        "bridge_y_min": _BRIDGE_Y_MIN,
        "bridge_y_max": _BRIDGE_Y_MAX,
        "bridge_z_min": _BRIDGE_Z_MIN,
        "bridge_z_max": _BRIDGE_Z_MAX,
        "retention_pocket_z": _RETENTION_POCKET_Z,
        "red_tongue_z": _RED_TONGUE_Z,
        "m3_insert_center_z": _M3_INSERT_CENTER_Z,
        "m3_insert_radius": _M3_INSERT_RADIUS,
        "insert_bridge": bridge,
        "transition_start": (_TRANSITION_START_X, _TRANSITION_START_Y_HALF, _TRANSITION_START_Z_HALF),
        "transition_taper": (_TRANSITION_TAPER_X, _TRANSITION_TAPER_Y_HALF, _TRANSITION_TAPER_Z_HALF),
        "blade_end": (_BLADE_END_X, _BLADE_END_Y_HALF, _BLADE_END_Z_HALF),
        "red_forecover_y": (_RED_FORECOVER_Y_MIN, _RED_FORECOVER_Y_MAX),
        "carrier_y": (_CARRIER_Y_MIN, _CARRIER_Y_MAX),
        "coxa_fork_entry_slots": _paired_y_boxes(_COXA_FORK_SLOT_X, _COXA_FORK_SLOT_Z),
        "knee_fork_exit_slots": _paired_y_boxes(_KNEE_FORK_SLOT_X, _KNEE_FORK_SLOT_Z),
        "fork_slot_y_band": (_FORK_SLOT_Y_INNER, _FORK_SLOT_Y_OUTER),
        "forecap_screw_axis": {
            "axis": "Y",
            "x": _FORECAP_SCREW_X,
            "z": _FORECAP_SCREW_Z,
            "y_start": _FORECAP_SCREW_Y_START,
            "y_end": _FORECAP_SCREW_Y_END,
            "length": _FORECAP_SCREW_LENGTH,
        },
        "forecap_key_tongue_y": _FORECAP_TONGUE_Y,
        "forecap_key_tongue_z": _FORECAP_TONGUE_Z,
        "femur_shell_z_half": _FEMUR_SHELL_Z_HALF,
        "relative_base_deg": _RELATIVE_BASE_DEG,
        "service_note": _SERVICE_NOTE,
        "centred_envelopes": centred_envelopes,
    }
