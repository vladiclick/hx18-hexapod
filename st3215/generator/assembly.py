"""Place every printed part, servo, electronics envelope and screw head for a given pose."""
from functools import lru_cache

import cadquery as cq

import layout
import parts as P
import servo
from scene import Part

WHITE = (0.90, 0.91, 0.92)
RED = (0.62, 0.10, 0.10)
CORE = (0.20, 0.21, 0.23)
RUBBER = (0.16, 0.16, 0.17)
STEEL = (0.62, 0.63, 0.65)
BATTERY = (0.14, 0.30, 0.66)
PCB = (0.06, 0.36, 0.22)
MODULE = (0.72, 0.73, 0.75)
XT60 = (0.95, 0.75, 0.10)

JOINTS = ('yaw', 'hip', 'knee')


@lru_cache(maxsize=None)
def shapes():
    """Every printed part, built once."""
    return dict(coxa=P.coxa().val(), coxa_cap=P.coxa_cap().val(), femur=P.femur().val(),
                femur_cover=P.femur_cover().val(), tibia=P.tibia().val(), toe_boot=P.toe_boot().val(),
                core_tub=P.core_tub().val(), core_lid=P.core_lid().val(), front_arrow=P.front_arrow().val(),
                battery_bay=P.battery_bay().val())


@lru_cache(maxsize=None)
def _screw(d_head, h_head, socket):
    head = cq.Workplane('XY').circle(d_head / 2).extrude(h_head).edges('>Z').fillet(0.3)
    return head.cut(cq.Workplane('XY', origin=(0, 0, h_head - socket * 0.6)).polygon(6, socket * 1.12)
                    .extrude(1)).val()


M3_HEAD = (5.5, 3.0, 2.5)
M2_HEAD = (3.8, 2.0, 1.5)


def _screw_parts(name, frame, spots, kind=M3_HEAD, link='core'):
    """Screw heads standing on the given (x, y, z, axis) seats; axis = '+z', '-z', '+y', '-y'."""
    head = _screw(*kind)
    turn = {'+z': cq.Location(), '-z': cq.Location(cq.Vector(), cq.Vector(1, 0, 0), 180),
            '+y': cq.Location(cq.Vector(), cq.Vector(1, 0, 0), -90),
            '-y': cq.Location(cq.Vector(), cq.Vector(1, 0, 0), 90)}
    return [Part(name, head, STEEL, frame * cq.Location(cq.Vector(x, y, z)) * turn[axis], 'hardware', metal=True,
                 link=link) for x, y, z, axis in spots]


def _horn_screws(frame, x, z_or_y, plane, link):
    out = []
    for dx, dv in P.HORN_HOLES:
        if plane == 'z':        # screws on the top (+z) and bottom (-z) bracket plates
            out += [(x + dx, dv, P.COXA_TOP - P.M3_HEAD_DEPTH, '+z'),
                    (x + dx, dv, P.COXA_BOTTOM + P.M3_HEAD_DEPTH, '-z')]
        else:                   # screws on the +y and -y plates, around (x, z)
            out += [(x + dx, layout.PLATE_OUT - P.M3_HEAD_DEPTH, z_or_y + dv, '+y'),
                    (x + dx, -layout.PLATE_OUT + P.M3_HEAD_DEPTH, z_or_y + dv, '-y')]
    return _screw_parts('M3 horn screw', frame, out, link=link)


def servo_parts(label, frame, horn_angle=0.0, link='core', horn_link='core'):
    """The servo case moves with `link`; its horns turn with the output (`horn_angle` about the servo axis)."""
    turn = cq.Location(cq.Vector(), cq.Vector(0, 0, 1), horn_angle)
    out = []
    for p in servo.load():
        horn = 'horn' in p.name
        out.append(Part(f'{label} / {p.name}', p.shape, p.color, frame * turn if horn else frame, 'servo',
                        metal=horn, link=horn_link if horn else link))
    return out


def leg(i, yaw=0.0, hip=0.0, knee=0.0):
    s = shapes()
    f = layout.frames(i, yaw, hip, knee)
    n = i + 1
    ids = [3 * i + 1, 3 * i + 2, 3 * i + 3]
    c, fe, ti = f'leg{n}/coxa', f'leg{n}/femur', f'leg{n}/tibia'
    out = [
        Part(f'Leg {n} coxa', s['coxa'], WHITE, f['coxa'], link=c),
        Part(f'Leg {n} coxa cap', s['coxa_cap'], RED, f['coxa'], link=c),
        Part(f'Leg {n} femur', s['femur'], WHITE, f['femur'], link=fe),
        Part(f'Leg {n} femur cover', s['femur_cover'], RED, f['femur'], link=fe),
        Part(f'Leg {n} tibia', s['tibia'], WHITE, f['tibia'], link=ti),
        Part(f'Leg {n} toe boot', s['toe_boot'], RUBBER, f['tibia'], link=ti),
    ]
    # the hip and knee servo axes are the link +y axes, so a joint angle a turns the horns by -a
    out += servo_parts(f'Leg {n} yaw servo ID {ids[0]} (ST3215)', f['leg'] * layout.YAW_SERVO, yaw, 'core', c)
    out += servo_parts(f'Leg {n} hip servo ID {ids[1]} (ST3215)', f['coxa'] * layout.HIP_SERVO, -hip, c, fe)
    out += servo_parts(f'Leg {n} knee servo ID {ids[2]} (ST3215)', f['femur'] * layout.KNEE_SERVO, -knee, fe, ti)
    out += _horn_screws(f['coxa'], 0, 0, 'z', c)
    out += _horn_screws(f['femur'], 0, 0, 'y', fe)
    out += _horn_screws(f['tibia'], 0, 0, 'y', ti)
    out += _screw_parts('M3 cap screw', f['coxa'], [(x, y, P.COXA_TOP - P.CAP_HEAD_DEPTH, '+z') for x, y in P.CAP_SCREWS],
                        link=c)
    out += _screw_parts('M3 cover screw', f['femur'],
                        [(x, y, P.F_HALF_H - P.COVER_HEAD_DEPTH, '+z') for x, y in P.COVER_SCREWS], link=fe)
    m2 = [(layout.L_COXA - P.SCREW_X, -layout.PLATE_OUT + P.M2_HEAD_DEPTH, layout.Z_MID + w, '-y')
          for w in (-P.SCREW_W, P.SCREW_W)]
    out += _screw_parts('M2 servo screw', f['coxa'], m2, M2_HEAD, link=c)
    m2 = [(layout.L_FEMUR - P.SCREW_X, -layout.PLATE_OUT + P.M2_HEAD_DEPTH, w, '-y') for w in (-P.SCREW_W, P.SCREW_W)]
    out += _screw_parts('M2 servo screw', f['femur'], m2, M2_HEAD, link=fe)
    return out


@lru_cache(maxsize=None)
def _electronics():
    battery = cq.Workplane('XY').box(35, 106, 25).edges('|Y').fillet(3).val()
    xt60 = cq.Workplane('XY').box(8, 16, 15).val()
    board = cq.Workplane('XY').box(65, 50, 1.6).edges('|Z').fillet(2).val()
    module = cq.Workplane('XY').box(18, 25.5, 3.2).translate((16, 0, 2.4)).val()
    header = cq.Workplane('XY').box(8, 30, 8).translate((-24, 0, 4.8)).val()
    return battery, xt60, board, module, header


def core():
    s = shapes()
    battery, xt60, board, module, header = _electronics()
    bay_floor = P.FLOOR_TOP - P.FLOOR - P.BAY_H + P.WALL
    board_z = P.FLOOR_TOP + 5.8
    lid_screws = [(*P._corner(k, P.CORE_R - 6.0), P.TUB_TOP + P.LID_T - P.M3_HEAD_DEPTH, '+z') for k in range(6)]
    bay_screws = [(x, y, P.FLOOR_TOP - P.FLOOR - 8.0, '-z') for x, y in P.BAY_SCREWS]
    yaw_screws = [(*P._polar(P.YAW_SCREWS_R, a, w), P.FLOOR_TOP - P.FLOOR + P.YAW_M2_HEAD_DEPTH, '-z')
                  for a in layout.LEG_ANGLES for w in (-P.SCREW_W, P.SCREW_W)]
    return [
        Part('Core tub', s['core_tub'], CORE, kind='printed'),
        Part('Core lid', s['core_lid'], CORE, kind='printed'),
        Part('Front arrow', s['front_arrow'], RED, kind='printed'),
        Part('Battery bay', s['battery_bay'], CORE, kind='printed'),
        Part('Battery 3S LiPo 2200 mAh (envelope)', battery, BATTERY, cq.Location(cq.Vector(0, 0, bay_floor + 12.5)),
             'electronics'),
        Part('XT60 connector', xt60, XT60, cq.Location(cq.Vector(30, 0, bay_floor + 7.5)), 'electronics'),
        Part('ESP32 bus-servo driver board (envelope)', board, PCB, cq.Location(cq.Vector(0, 0, board_z)),
             'electronics'),
        Part('ESP32 module', module, MODULE, cq.Location(cq.Vector(0, 0, board_z)), 'electronics', metal=True),
        Part('Servo bus header', header, (0.08, 0.08, 0.09), cq.Location(cq.Vector(0, 0, board_z)), 'electronics'),
    ] + (_screw_parts('M3 lid screw', cq.Location(), lid_screws)
         + _screw_parts('M3 bay screw', cq.Location(), bay_screws)
         + _screw_parts('M2 servo screw', cq.Location(), yaw_screws, M2_HEAD))


def robot(pose=None, legs=range(6)):
    pose = pose or layout.STAND
    out = core()
    for i in legs:
        out += leg(i, **(pose[i] if isinstance(pose, (list, tuple)) else pose))
    return out


def on_ground(parts_list, height=None):
    """Move everything up so the feet stand on z = 0 (stand pose height unless given)."""
    lift = cq.Location(cq.Vector(0, 0, layout.stand_height() if height is None else height))
    for p in parts_list:
        p.loc = lift * p.loc
    return parts_list
