"""The whole robot as a flat list of placed, coloured parts (scene.Part)."""
from functools import lru_cache

import cadquery as cq

import layout
import parts as P
import servo
from scene import Part

# the concept's Fusion colours
WHITE = (220 / 255, 224 / 255, 225 / 255)
CORE = (46 / 255, 49 / 255, 54 / 255)
RED = (156 / 255, 54 / 255, 46 / 255)
FOOT = (225 / 255, 225 / 255, 220 / 255)
RESERVE = (108 / 255, 118 / 255, 130 / 255)
SCREW = (42 / 255, 45 / 255, 48 / 255)

COLOURS = dict(CoreTub=CORE, CoreLid=CORE, ElectronicsCassette=CORE, CoxaCarrier=WHITE, FemurCarrier=WHITE,
               FemurCheek=RED, Tibia=WHITE, FootPad=FOOT)
NAMES = dict(CoreTub='Core tub', CoreLid='Core lid', ElectronicsCassette='Electronics cassette',
             CoxaCarrier='coxa', FemurCarrier='femur', FemurCheek='femur cover', Tibia='tibia',
             FootPad='foot pad')


@lru_cache(maxsize=None)
def shapes():
    return {k: fn().solid() for k, fn in P.PRINTS.items()}


def _servo_frames():
    """ST3215 frames (servo.py) in their link frames."""
    def frame(origin, x, z):
        from OCP.gp import gp_Ax3, gp_Dir, gp_Pnt, gp_Trsf
        t = gp_Trsf()
        t.SetTransformation(gp_Ax3(gp_Pnt(*origin), gp_Dir(*z), gp_Dir(*x)), gp_Ax3())
        return cq.Location(t)
    return dict(
        yaw=frame((0, 0, layout.YAW_HORN_Z), (-1, 0, 0), (0, 0, 1)),                 # in the leg base frame
        hip=frame((0, layout.HORN_Y, 0), (1, 0, 0), (0, 1, 0)),                       # in the femur frame
        knee=frame((layout.FEMUR, layout.HORN_Y, 0), (-1, 0, 0), (0, 1, 0)),          # in the femur frame
    )


SERVO_FRAMES = _servo_frames()


@lru_cache(maxsize=None)
def _screw(length, head_h=3.0, head_r=2.75):
    """Socket screw along +Z, head on top of z=0, shank down to -length."""
    shank = cq.Solid.makeCylinder(1.5, length, cq.Vector(0, 0, -length))
    head = cq.Solid.makeCylinder(head_r, head_h, cq.Vector(0, 0, 0))
    return shank.fuse(head).clean()


def _z_down(x, y, z):
    """Screw pointing up (+Z) with its head under z."""
    return cq.Location(cq.Vector(x, y, z), cq.Vector(1, 0, 0), 180)


def servo_parts(label, link, case_loc, horn_link, horn_loc):
    out = []
    for sp in servo.load():
        horn = 'horn' in sp.name
        out.append(Part(f'{label} / {sp.name}', sp.shape, sp.color, horn_loc if horn else case_loc, 'servo',
                        metal=horn, link=horn_link if horn else link))
    return out


def leg(i, yaw=0.0, hip=0.0, knee=0.0):
    n = i + 1
    sh = shapes()
    f = layout.frames(i, yaw, hip, knee)
    f0 = layout.frames(i)
    links = {k: f'leg{n}/{k}' for k in ('coxa', 'femur', 'tibia')}
    out = []
    for key, link in (('CoxaCarrier', 'coxa'), ('FemurCarrier', 'femur'), ('FemurCheek', 'femur'),
                      ('Tibia', 'tibia'), ('FootPad', 'tibia')):
        out.append(Part(f'Leg {n} {NAMES[key]}', sh[key], COLOURS[key], f[link], link=links[link]))
    ids = (3 * n - 2, 3 * n - 1, 3 * n)
    # yaw: case on the core, horn on the coxa
    yaw_case = f['base'] * SERVO_FRAMES['yaw']
    yaw_horn = f['coxa'] * SERVO_FRAMES['yaw']
    out += servo_parts(f'Leg {n} yaw servo ID {ids[0]}', 'core', yaw_case, links['coxa'], yaw_horn)
    # hip: case in the femur (inverted mounting), horns bolted to the coxa plates
    hip_case = f['femur'] * SERVO_FRAMES['hip']
    hip_horn = f['coxa'] * layout.rel(f0['coxa'], f0['femur']) * SERVO_FRAMES['hip']
    out += servo_parts(f'Leg {n} hip servo ID {ids[1]}', links['femur'], hip_case, links['coxa'], hip_horn)
    # knee: case in the femur, horns bolted to the tibia plates
    knee_case = f['femur'] * SERVO_FRAMES['knee']
    knee_horn = f['tibia'] * layout.rel(f0['tibia'], f0['femur']) * SERVO_FRAMES['knee']
    out += servo_parts(f'Leg {n} knee servo ID {ids[2]}', links['femur'], knee_case, links['tibia'], knee_horn)
    # the concept's rear service screw of the red cover, now M3 x 45 over the servos
    loc = f['femur'] * cq.Location(cq.Vector(P.SCREW_X, layout.S * -18.7 + 3.2, P.SCREW_Z), cq.Vector(1, 0, 0), 90)
    out.append(Part(f'Leg {n} cover screw M3x45', _screw(45.0), SCREW, loc, 'hardware', link=links['femur']))
    return out


def core():
    sh = shapes()
    out = [Part(NAMES[k], sh[k], COLOURS[k]) for k in ('CoreTub', 'CoreLid', 'ElectronicsCassette')]
    for key, w, d, z0, h, angle in P.electronics_reserves():
        box = cq.Solid.makeBox(w, d, h, cq.Vector(-w / 2, -d / 2, z0)).rotate((0, 0, 0), (0, 0, 1), angle)
        out.append(Part(key.replace('Reserve', ' keep-out'), box, RESERVE, kind='electronics'))
    s = layout.S
    for k, (x, y) in enumerate(P._scaled(P.lid_fasteners(), s), 1):
        out.append(Part(f'Lid screw M3x40 {k}', _screw(40.0), SCREW, _z_down(x, y, -32 * s + 3.2), 'hardware'))
    for k, (x, y) in enumerate(P.cassette_fasteners(), 1):
        loc = cq.Location(cq.Vector(x, y, -15 * s + 2 * s))
        out.append(Part(f'Cassette screw M3x6 {k}', _screw(6.0, 1.8, 2.8), SCREW, loc, 'hardware'))
    return out


def robot(poses=None, legs=range(layout.LEGS)):
    poses = poses or [dict()] * layout.LEGS
    out = core()
    for i in legs:
        out += leg(i, **poses[i])
    return out


def on_ground(parts_list):
    """Shift everything so the lowest point of the modelled pose sits at z = 0."""
    low = min(layout.foot_point(i).z for i in range(layout.LEGS)) - 5.5 * layout.S
    return [Part(p.name, p.shape, p.color, cq.Location(cq.Vector(0, 0, -low)) * p.loc, p.kind, p.metal, p.link)
            for p in parts_list]
