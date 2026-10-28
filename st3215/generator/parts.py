"""Printed parts of HX18 ST3215, each modelled in its own link frame (see layout.py)."""
import math

import cadquery as cq

import servo
from layout import (CLEAR, HORN_FACE, HUB_R, L_COXA, L_FEMUR, LEG_ANGLES, PLATE, PLATE_OUT, R_YAW,
                    SHANK, TIBIA_BEND, TIBIA_BEND_Z, Z_MID)

M3_CLEAR, M3_HEAD, M3_HEAD_DEPTH = 3.4, 6.2, 1.5
M2_CLEAR, M2_HEAD, M2_HEAD_DEPTH = 2.4, 4.4, 2.0
CAP_HEAD_DEPTH = 6.0                # coxa cap: deep counterbores so M3 x 10 reach the sleeve walls
COVER_HEAD_DEPTH = 1.0              # femur cover: keep 2 mm under the head
YAW_M2_HEAD_DEPTH = 1.0             # yaw servo screws through the 3 mm tub floor
M3_PILOT = 2.8                      # self-tapping / heat-set pilot
HORN_HOLES = [(7.0, 0.0), (-7.0, 0.0), (0.0, 7.0), (0.0, -7.0)]
BOSS_RECESS_D, BOSS_RECESS_DEPTH = 11.0, 0.9   # idler side: the case bushing stands 0.55 mm proud of the horn

# servo case faces in a link whose servo axis is +y (drive horn face at y = HORN_FACE)
CASE_TOP = servo.TOP_FACE_Z + HORN_FACE          # +y face (top case): 16.53
CASE_BOTTOM = -(servo.BOTTOM_FACE_Z + HORN_FACE)  # -y face (bottom case): 16.57 below the mid-plane
HALF_W = servo.CASE_Y[1] + CLEAR                  # 12.8: half width of the case + clearance
LONG = servo.CASE_X[1]                            # 35.1: axis -> long end
SHORT = -servo.CASE_X[0]                          # 10.15: axis -> short end
SCREW_X = 32.8                                    # bottom-face M2 holes, distance from the axis
SCREW_W = 10.2


# ---------------------------------------------------------------- helpers
def hull_profile(r, u0, u1, h, angle=0.0, center=(0.0, 0.0)):
    """Closed XY wire: hull of a circle (radius r at `center`) and the rectangle u0..u1 x -h..h,
    where u runs along direction `angle` (degrees) from the centre."""
    a = math.radians(angle)
    ca, sa = math.cos(a), math.sin(a)

    def xy(u, v):
        return (center[0] + u * ca - v * sa, center[1] + u * sa + v * ca)

    def tangent(sign):
        cu, cv = u0, sign * h
        d = math.hypot(cu, cv)
        t = math.atan2(cv, cu) + sign * math.acos(min(1.0, r / d))
        return r * math.cos(t), r * math.sin(t)

    tp, tm = tangent(1), tangent(-1)
    wp = (cq.Workplane('XY').moveTo(*xy(*tp)).lineTo(*xy(u0, h)).lineTo(*xy(u1, h))
          .lineTo(*xy(u1, -h)).lineTo(*xy(u0, -h)).lineTo(*xy(*tm))
          .threePointArc(xy(-r, 0.0), xy(*tp)).close())
    return wp


def extrude_z(wp, z0, z1):
    return wp.extrude(z1 - z0).translate((0, 0, z0))


def extrude_y(wp, y0, y1):
    """Extrude an XY wire whose v axis should become +z, over y0..y1."""
    return wp.extrude(y1 - y0).rotate((0, 0, 0), (1, 0, 0), 90).translate((0, y1, 0))


def box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane('XY').box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))


def cyl_y(x, z, d, y0, y1):
    return cq.Workplane('XZ', origin=(0, y1, 0)).center(x, z).circle(d / 2).extrude(y1 - y0)


def cyl_z(x, y, d, z0, z1):
    return cq.Workplane('XY', origin=(0, 0, z0)).center(x, y).circle(d / 2).extrude(z1 - z0)


def horn_holes_y(solid, x, z, y_out, inward, recess=False):
    """M3 horn screws through a plate whose outer face is at y_out; `inward` = +1 or -1 (towards the servo)."""
    y_in = y_out + inward * PLATE
    lo, hi = sorted((y_out, y_in))
    for dx, dz in HORN_HOLES:
        solid = solid.cut(cyl_y(x + dx, z + dz, M3_CLEAR, lo - 1, hi + 1))
        h0, h1 = sorted((y_out, y_out + inward * M3_HEAD_DEPTH))
        solid = solid.cut(cyl_y(x + dx, z + dz, M3_HEAD, h0 - 1 if inward > 0 else h0, h1 if inward > 0 else h1 + 1))
    solid = solid.cut(cyl_y(x, z, 5.0, lo - 1, hi + 1))
    if recess:
        r0, r1 = sorted((y_in, y_in - inward * BOSS_RECESS_DEPTH))
        solid = solid.cut(cyl_y(x, z, BOSS_RECESS_D, r0, r1))
    return solid


def horn_holes_z(solid, x, y, z_out, inward, recess=False):
    z_in = z_out + inward * PLATE
    lo, hi = sorted((z_out, z_in))
    for dx, dy in HORN_HOLES:
        solid = solid.cut(cyl_z(x + dx, y + dy, M3_CLEAR, lo - 1, hi + 1))
        h0, h1 = sorted((z_out, z_out + inward * M3_HEAD_DEPTH))
        solid = solid.cut(cyl_z(x + dx, y + dy, M3_HEAD, h0 - (1 if inward > 0 else 0), h1 + (0 if inward > 0 else 1)))
    solid = solid.cut(cyl_z(x, y, 5.0, lo - 1, hi + 1))
    if recess:
        r0, r1 = sorted((z_in, z_in - inward * BOSS_RECESS_DEPTH))
        solid = solid.cut(cyl_z(x, y, BOSS_RECESS_D, r0, r1))
    return solid


def pad_recess(axis_x, axis_z=0.0):
    """Recess in a -y side wall for the raised pad on the servo bottom face (servo body along -x)."""
    x0, x1, w, z = servo.BOTTOM_PAD
    depth = servo.BOTTOM_FACE_Z - z
    return box(axis_x - x1 - CLEAR, axis_x - x0 + CLEAR, -CASE_BOTTOM - CLEAR - depth - CLEAR, -CASE_BOTTOM,
               axis_z - w - CLEAR, axis_z + w + CLEAR)


def fillet(wp, selector, r):
    try:
        out = wp.edges(selector).fillet(r)
        return out if out.val().isValid() else wp
    except Exception:
        return wp


# ---------------------------------------------------------------- coxa
# coxa frame = leg frame turned by the yaw angle; the hip servo axis is at (L_COXA, 0, Z_MID)
COXA_TOP = PLATE                                   # 4.0
COXA_BOTTOM = servo.IDLER_HORN_Z[0] - PLATE        # -41.25
WEB_X = (17.0, 21.0)                               # clears the yaw case corner, 16.0 from the axis
SLEEVE_X1 = L_COXA - 16.5                          # 40: stays outside the femur hub sweep
SLEEVE_TOP = Z_MID + HALF_W                        # -5.83: the red cap closes the sleeve above this


def _coxa_outline():
    return hull_profile(HUB_R, WEB_X[0], SLEEVE_X1, PLATE_OUT)


def coxa():
    top_arm = extrude_z(_coxa_outline(), 0.0, COXA_TOP).intersect(box(-20, WEB_X[1], -30, 30, -1, 10))
    bottom_arm = extrude_z(_coxa_outline(), COXA_BOTTOM, servo.IDLER_HORN_Z[0]).intersect(
        box(-20, WEB_X[1], -30, 30, -50, 0))
    web = box(WEB_X[0], WEB_X[1], -PLATE_OUT, PLATE_OUT, COXA_BOTTOM, COXA_TOP)
    sleeve = box(WEB_X[1], SLEEVE_X1, -PLATE_OUT, PLATE_OUT, COXA_BOTTOM, SLEEVE_TOP)
    body = top_arm.union(bottom_arm).union(web).union(sleeve)
    body = fillet(body, '|Z and >X', 2.0)
    # hip servo pocket, open at the top (cap) and at the front (horns)
    pocket = box(WEB_X[1], SLEEVE_X1 + 1, -CASE_BOTTOM - CLEAR, CASE_TOP + CLEAR, Z_MID - HALF_W, SLEEVE_TOP + 1)
    body = body.cut(pocket).cut(pad_recess(L_COXA, Z_MID))
    # cable slot through the web for the hip servo leads
    body = body.cut(box(WEB_X[0] - 1, WEB_X[1] + 1, -7, 7, Z_MID - 8, Z_MID + 8))
    # yaw horns: drive on top, idler below
    body = horn_holes_z(body, 0, 0, COXA_TOP, -1)
    body = horn_holes_z(body, 0, 0, COXA_BOTTOM, +1, recess=True)
    # hip servo: two M2 screws into the bottom-case holes, from the -y side
    for dz in (-SCREW_W, SCREW_W):
        sx = L_COXA - SCREW_X
        body = body.cut(cyl_y(sx, Z_MID + dz, M2_CLEAR, -PLATE_OUT - 1, -CASE_BOTTOM))
        body = body.cut(cyl_y(sx, Z_MID + dz, M2_HEAD, -PLATE_OUT - 1, -PLATE_OUT + M2_HEAD_DEPTH))
    for x, y in CAP_SCREWS:
        body = body.cut(cyl_z(x, y, M3_PILOT, SLEEVE_TOP - 8, SLEEVE_TOP + 1))
    return body


CAP_SCREWS = [(25.0, 19.8), (25.0, -19.8), (36.0, 19.8), (36.0, -19.8)]


def coxa_cap():
    cap = extrude_z(_coxa_outline(), SLEEVE_TOP, COXA_TOP).intersect(box(WEB_X[1], 60, -30, 30, -20, 10))
    cap = fillet(cap, '>Z', 1.2)
    for x, y in CAP_SCREWS:
        cap = cap.cut(cyl_z(x, y, M3_CLEAR, SLEEVE_TOP - 1, COXA_TOP + 1))
        cap = cap.cut(cyl_z(x, y, M3_HEAD, COXA_TOP - CAP_HEAD_DEPTH, COXA_TOP + 1))
    return cap


# ---------------------------------------------------------------- femur
# femur frame: origin on the hip axis, x towards the knee, y = servo axis, z up at hip = 0
F_HALF_H = HALF_W + 3.0                       # 15.8
F_SHELL_X0 = L_FEMUR - LONG - CLEAR - 3.0     # 23.5: end wall behind the knee servo
F_SIDE_X1 = L_FEMUR - 24.0                    # 38: side walls stop here so the tibia can fold back
F_TONGUE_X1 = L_FEMUR - 17.5                  # 44.5: top and bottom tongues over the servo
F_TONGUE_Y = HORN_FACE - 0.4                  # 18.2: inside the tibia plates
COVER_Z = HALF_W                              # 12.8: the red cover sits on the knee servo case
COVER_SCREWS = [(27.0, 19.8), (27.0, -19.8), (35.0, 19.8), (35.0, -19.8)]


def _cover_outline():
    # full width over the side walls, then a tongue that stays inside the tibia plates
    return (cq.Workplane('XY').moveTo(F_SHELL_X0, -PLATE_OUT).lineTo(F_SIDE_X1, -PLATE_OUT)
            .lineTo(F_SIDE_X1, -F_TONGUE_Y).lineTo(F_TONGUE_X1, -F_TONGUE_Y).lineTo(F_TONGUE_X1, F_TONGUE_Y)
            .lineTo(F_SIDE_X1, F_TONGUE_Y).lineTo(F_SIDE_X1, PLATE_OUT).lineTo(F_SHELL_X0, PLATE_OUT).close())


def femur():
    def outline():
        return hull_profile(HUB_R, F_SHELL_X0, F_SIDE_X1, F_HALF_H)
    plates = extrude_y(outline(), HORN_FACE, PLATE_OUT).union(extrude_y(outline(), -PLATE_OUT, -HORN_FACE))
    shell = box(F_SHELL_X0, F_SIDE_X1, -PLATE_OUT, PLATE_OUT, -F_HALF_H, F_HALF_H)
    bottom_tongue = extrude_z(_cover_outline(), -F_HALF_H, -COVER_Z)
    body = plates.union(shell).union(bottom_tongue)
    body = fillet(body, '|Y and <Z', 1.5)
    # knee servo pocket (open on top for assembly, closed by the red cover)
    body = body.cut(box(F_SHELL_X0 + 3.0, F_TONGUE_X1 + 30, -CASE_BOTTOM - CLEAR, CASE_TOP + CLEAR,
                        -HALF_W, F_HALF_H + 1))
    body = body.cut(pad_recess(L_FEMUR))
    body = body.cut(extrude_z(_cover_outline(), COVER_Z, F_HALF_H + 1))
    body = body.cut(box(F_SIDE_X1, F_TONGUE_X1 + 30, -F_TONGUE_Y, F_TONGUE_Y, -HALF_W, F_HALF_H + 1))
    # cable slot in the end wall
    body = body.cut(box(F_SHELL_X0 - 1, F_SHELL_X0 + 4, -7, 7, -8, 8))
    # hip horns
    body = horn_holes_y(body, 0, 0, PLATE_OUT, -1)
    body = horn_holes_y(body, 0, 0, -PLATE_OUT, +1, recess=True)
    # knee servo screws, bottom-case holes on the -y side
    for dz in (-SCREW_W, SCREW_W):
        sx = L_FEMUR - SCREW_X
        body = body.cut(cyl_y(sx, dz, M2_CLEAR, -PLATE_OUT - 1, -CASE_BOTTOM))
        body = body.cut(cyl_y(sx, dz, M2_HEAD, -PLATE_OUT - 1, -PLATE_OUT + M2_HEAD_DEPTH))
    for x, y in COVER_SCREWS:
        body = body.cut(cyl_z(x, y, M3_PILOT, COVER_Z - 8, COVER_Z + 1))
    return body


def femur_cover():
    cover = extrude_z(_cover_outline(), COVER_Z, F_HALF_H)
    cover = fillet(cover, '|Z', 3.0)
    cover = fillet(cover, '>Z', 1.0)
    for x, y in COVER_SCREWS:
        cover = cover.cut(cyl_z(x, y, M3_CLEAR, COVER_Z - 1, F_HALF_H + 1))
        cover = cover.cut(cyl_z(x, y, M3_HEAD, F_HALF_H - COVER_HEAD_DEPTH, F_HALF_H + 1))
    return cover


# ---------------------------------------------------------------- tibia
# tibia frame: origin on the knee axis, y = servo axis; straight down to the bend, then the shank
T_BLOCK_Z = (TIBIA_BEND_Z - 4.0, -28.0)   # solid block between the plates, clear of the knee servo case
BOOT_LEN = 22.0                           # toe boot length along the shank
BOOT_R = 10.0


def _rounded_rect(w, h, r):
    return cq.Sketch().rect(w, h).vertices().fillet(r)


def _on_shank(wp):
    """Move a solid modelled along -z from the bend point onto the bent shank axis."""
    return wp.rotate((0, 0, 0), (0, 1, 0), TIBIA_BEND).translate((0, 0, TIBIA_BEND_Z))


def tibia():
    def arm():
        return hull_profile(HUB_R, -T_BLOCK_Z[1], -T_BLOCK_Z[0], HUB_R, angle=-90)
    tib = extrude_y(arm(), HORN_FACE, PLATE_OUT).union(extrude_y(arm(), -PLATE_OUT, -HORN_FACE))
    block = box(-HUB_R, HUB_R, -PLATE_OUT, PLATE_OUT, *T_BLOCK_Z)
    tib = tib.union(fillet(block, '|Y and <Z', 4.0))
    end = -(SHANK - BOOT_LEN)
    sections = [(0.0, 2 * HUB_R, 2 * PLATE_OUT, 4.0), (-26.0, 21.0, 30.0, 5.0), (end, 15.0, 19.0, 5.0)]
    shank = (cq.Workplane('XY')
             .placeSketch(*[_rounded_rect(w, d, r).moved(cq.Location(cq.Vector(0, 0, z))) for z, w, d, r in sections])
             .loft(ruled=False))
    slot = cq.Workplane('YZ', origin=(-30, 0, 0)).center(0, end / 2 + 2).slot2D(40.0, 8.0, 90).extrude(60)
    shank = shank.cut(slot).union(cyl_z(0, 0, 11.0, end - 12.0, end + 0.5))
    tib = tib.union(_on_shank(shank))
    tib = horn_holes_y(tib, 0, 0, PLATE_OUT, -1)
    tib = horn_holes_y(tib, 0, 0, -PLATE_OUT, +1, recess=True)
    return tib


def toe_boot():
    tip, top = -SHANK, -(SHANK - BOOT_LEN)
    boot = (cq.Workplane('XY').sphere(BOOT_R).translate((0, 0, tip + BOOT_R))
            .union(cyl_z(0, 0, 2 * BOOT_R, tip + BOOT_R, top - 0.2)))
    boot = fillet(boot, '>Z', 2.0)
    boot = boot.cut(cyl_z(0, 0, 11.4, top - 12.3, top + 1))
    return _on_shank(boot)


# ---------------------------------------------------------------- core
# robot frame, z = 0 in the yaw drive-horn faces
CORE_R = R_YAW - HUB_R - 1.5          # 66: hexagon in-radius, clear of the coxa hubs
FLOOR_TOP = servo.BOTTOM_FACE_Z - CLEAR   # -35.6
FLOOR = 3.0
TUB_TOP = servo.TOP_FACE_Z + 0.3      # -1.8: the lid presses on the yaw servos
LID_T = 4.0
WALL = 2.5
BAY_R = 58.0
BAY_H = 30.0
YAW_SCREWS_R = R_YAW - SCREW_X        # 47.2
BAY_SCREWS = [(52.0 * math.cos(math.radians(a)), 52.0 * math.sin(math.radians(a))) for a in range(0, 360, 60)]


def _hexagon(r_in, z0, z1):
    # flats face the legs (30 deg + k * 60)
    return (cq.Workplane('XY', origin=(0, 0, z0)).polygon(6, 2 * r_in / math.cos(math.pi / 6))
            .extrude(z1 - z0))


def _per_leg(shape_fn):
    out = None
    for a in LEG_ANGLES:
        s = shape_fn().rotate((0, 0, 0), (0, 0, 1), a)
        out = s if out is None else out.union(s)
    return out


def core_tub():
    z0 = FLOOR_TOP - FLOOR
    tub = _hexagon(CORE_R, z0, TUB_TOP)
    tub = fillet(tub, '|Z', 6.0)
    tub = tub.cut(_hexagon(CORE_R - WALL, FLOOR_TOP, TUB_TOP + 1))
    # yaw servo slots through the walls, pockets for the raised label pad under each servo
    tub = tub.cut(_per_leg(lambda: box(R_YAW - LONG - CLEAR, R_YAW + 20, -HALF_W, HALF_W, FLOOR_TOP, TUB_TOP + 1)))
    pad_x0, pad_x1, pad_w, pad_z = servo.BOTTOM_PAD
    tub = tub.cut(_per_leg(lambda: box(R_YAW - pad_x1 - CLEAR, R_YAW - pad_x0 + CLEAR, -pad_w - CLEAR, pad_w + CLEAR,
                                       pad_z - CLEAR, FLOOR_TOP + 1)))
    # side rails that locate each yaw servo
    rail = lambda: (box(R_YAW - LONG - 1.0, CORE_R - WALL + 0.1, HALF_W, HALF_W + 2.0, FLOOR_TOP - 0.1, -14.0)
                    .union(box(R_YAW - LONG - 1.0, CORE_R - WALL + 0.1, -HALF_W - 2.0, -HALF_W, FLOOR_TOP - 0.1, -14.0)))
    tub = tub.union(_per_leg(rail))
    # yaw servo M2 screws from below, lid screw bosses in the corners
    for a in LEG_ANGLES:
        for w in (-SCREW_W, SCREW_W):
            x, y = _polar(YAW_SCREWS_R, a, w)
            tub = tub.cut(cyl_z(x, y, M2_CLEAR, z0 - 1, FLOOR_TOP + 1))
            tub = tub.cut(cyl_z(x, y, M2_HEAD, z0 - 1, z0 + YAW_M2_HEAD_DEPTH))
    for k in range(6):
        x, y = _corner(k, CORE_R - 6.0)
        tub = tub.union(cyl_z(x, y, 8.0, FLOOR_TOP - 0.1, TUB_TOP).cut(cyl_z(x, y, M3_PILOT, FLOOR_TOP, TUB_TOP + 1)))
    # controller standoffs
    for x, y in ((-28, -20), (-28, 20), (28, -20), (28, 20)):
        tub = tub.union(cyl_z(x, y, 6.0, FLOOR_TOP - 0.1, FLOOR_TOP + 5.0)).cut(cyl_z(x, y, 2.2, FLOOR_TOP, FLOOR_TOP + 6))
    # cable pass to the battery bay, and bosses for the bay screws
    tub = tub.cut(box(-40, -30, -8, 8, z0 - 1, FLOOR_TOP + 1))
    for x, y in BAY_SCREWS:
        tub = tub.union(cyl_z(x, y, 8.0, FLOOR_TOP - 0.1, FLOOR_TOP + 6.0))
        tub = tub.cut(cyl_z(x, y, M3_PILOT, z0 - 1, FLOOR_TOP + 6.5))
    return tub


def _polar(r, angle_deg, tangential=0.0):
    a = math.radians(angle_deg)
    return (r * math.cos(a) - tangential * math.sin(a), r * math.sin(a) + tangential * math.cos(a))


def _corner(k, r_in):
    a = math.radians(k * 60.0)
    rc = r_in / math.cos(math.pi / 6)
    return rc * math.cos(a), rc * math.sin(a)


def core_lid():
    lid = _hexagon(CORE_R, TUB_TOP, TUB_TOP + LID_T)
    lid = fillet(lid, '|Z', 6.0)
    lid = fillet(lid, '>Z', 2.0)
    # raised centre plate
    lid = lid.union(_hexagon(CORE_R - 16.0, TUB_TOP + LID_T - 0.5, TUB_TOP + LID_T + 2.5).edges('|Z').fillet(4.0))
    for k in range(6):
        x, y = _corner(k, CORE_R - 6.0)
        lid = lid.cut(cyl_z(x, y, M3_CLEAR, TUB_TOP - 1, TUB_TOP + 10))
        lid = lid.cut(cyl_z(x, y, M3_HEAD, TUB_TOP + LID_T - M3_HEAD_DEPTH, TUB_TOP + 10))
    # front marker recess (the red arrow sits in it)
    lid = lid.cut(extrude_z(_arrow(), TUB_TOP + LID_T + 1.5, TUB_TOP + LID_T + 3))
    return lid


def _arrow():
    return (cq.Workplane('XY').moveTo(44, 0).lineTo(30, 11).lineTo(30, 5).lineTo(18, 5)
            .lineTo(18, -5).lineTo(30, -5).lineTo(30, -11).close())


def front_arrow():
    return extrude_z(_arrow().offset2D(-0.2), TUB_TOP + LID_T + 1.5, TUB_TOP + LID_T + 2.5)


def battery_bay():
    z1 = FLOOR_TOP - FLOOR
    z0 = z1 - BAY_H
    bay = _hexagon(BAY_R, z0, z1)
    bay = fillet(bay, '|Z', 6.0)
    bay = fillet(bay, '<Z', 3.0)
    bay = bay.cut(_hexagon(BAY_R - WALL, z0 + WALL, z1 + 1))
    for x, y in BAY_SCREWS:      # corner pillars, screwed from below into the tub floor
        bay = bay.union(cyl_z(x, y, 9.0, z0 + 1, z1).intersect(_hexagon(BAY_R - 0.5, z0, z1)))
        bay = bay.cut(cyl_z(x, y, M3_CLEAR, z0 - 1, z1 + 1))
        bay = bay.cut(cyl_z(x, y, M3_HEAD, z0 - 1, z1 - 8.0))
    # power switch cut-out at the rear
    bay = bay.cut(box(-BAY_R - 5, -BAY_R + 5, -9.5, 9.5, z0 + 9, z0 + 22))
    return bay
