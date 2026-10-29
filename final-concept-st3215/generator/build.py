"""Build every output of the HX18 final concept with ST3215 servos into the folder above.

    python build.py             # STEP, STLs, BOMs and VALIDATION.json
    python build.py --renders   # also the PNGs (needs node with three and playwright-core, and Chrome;
                                #   HX18_NODE_MODULES=<node_modules folder>)
    python build.py --gif       # the walking GIF (same requirements)
"""
import argparse
import csv
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import cadquery as cq

import assembly as A
import gait
import layout
import parts as P
import scene

OUT = Path(__file__).resolve().parents[1]
GEN = Path(__file__).resolve().parent
NAME = 'hx18-final-concept-st3215'
# tripod gait inside the concept's free joint travel; 2 x stride per cycle = one floor tile, so the GIF loops
GAIT = dict(frames=40, stride=50.0, lift=18.0, heading=90.0)
GIF_VIEW = dict(dir='0.95,0.5,0.38', dist=1120, height=65)

# part, quantity, material, colour, bed normal (as in final-concept/PRINT-BOM.csv)
PRINTS = [
    ('CoreTub', 1, 'PETG', 'charcoal', 'z'),
    ('CoreLid', 1, 'PETG', 'charcoal', 'z'),
    ('ElectronicsCassette', 1, 'PETG', 'charcoal', 'z'),
    ('CoxaCarrier', 6, 'PETG', 'white', 'z'),
    ('FemurCarrier', 6, 'PETG', 'white', '-y'),
    ('FemurCheek', 6, 'PLA', 'red', 'y'),
    ('Tibia', 6, 'PETG', 'white', 'y'),
    ('FootPad', 6, 'TPU 95A', 'white', 'y'),
]
DENSITY = {'PETG': 1.27, 'PLA': 1.24, 'TPU 95A': 1.21}

HARDWARE = [
    ('Waveshare ST3215 serial bus servo, 12 V', 18, '6 yaw (in the core), 6 hip and 6 knee (in the femurs); IDs 1-18'),
    ('M3 x 12 socket head screw (DIN 912)', 24, '4 per coxa, through the yaw cap into the yaw servo horn'),
    ('M3 x 6 button head screw (ISO 7380)', 48, '4 per hip and knee drive horn'),
    ('M3 x 5 button head screw (ISO 7380)', 48, '4 per hip and knee idler horn (3.35 mm thick)'),
    ('M3 x 45 socket head screw (DIN 912)', 6, 'rear screw of each red femur cover, passes over the servos'),
    ('M3 x 40 socket head screw (DIN 912)', 4, 'core lid, from underneath'),
    ('M3 x 6 screw', 2, 'electronics cassette'),
    ('M3 heat-set insert, 4.2 mm hole', 12, '4 lid bosses, 2 cassette columns, 6 femur cover tongues'),
    ('M2 x 12 screw', 18, '3 per femur: hip servo case (2) and knee servo case (1), from the back'),
    ('M2 x 14 screw', 24, '4 per yaw servo, through the tub floor'),
    ('Battery', 1, 'keep-out 60 x 32 x 18 mm under the cassette (the concept\'s, scaled)'),
    ('ESP32 with a serial bus servo interface', 1, 'keep-out 73 x 34 x 11 mm under the lid'),
    ('Regulator, if the controller needs one', 1, 'keep-out 44 x 44 x 14 mm'),
]


def print_ready(key, bed):
    shape = A.shapes()[key]
    if bed == '-y':
        shape = shape.rotate((0, 0, 0), (1, 0, 0), 90)      # rear face down
    elif bed == 'y':
        shape = shape.rotate((0, 0, 0), (1, 0, 0), -90)     # front face down
    bb = shape.BoundingBox()
    return shape.translate(cq.Vector(-(bb.xmin + bb.xmax) / 2, -(bb.ymin + bb.ymax) / 2, -bb.zmin))


def export_prints():
    (OUT / 'STL').mkdir(exist_ok=True)
    rows = []
    for key, qty, material, colour, bed in PRINTS:
        shape = print_ready(key, bed)
        scene.export_stl(shape, OUT / 'STL' / f'{key}.stl')
        bb = shape.BoundingBox()
        vol = shape.Volume() / 1000.0
        rows.append(dict(part=key, file=f'STL/{key}.stl', qty=qty, material=material, colour=colour,
                         volume_cm3=round(vol, 1), solid_mass_g=round(vol * DENSITY[material], 1),
                         bed_size_mm=f'{bb.xlen:.0f} x {bb.ylen:.0f} x {bb.zlen:.0f}'))
    with open(OUT / 'PRINT-BOM.csv', 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    with open(OUT / 'HARDWARE-BOM.csv', 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['item', 'qty', 'note'])
        w.writerows(HARDWARE)
    return rows


LEG_NAMES = [f'{int(layout.leg_angle(i))} deg' for i in range(layout.LEGS)]


def export_cad(parts):
    scene.export_step(parts, OUT / f'{NAME}.step', LEG_NAMES, name='HX18 final concept ST3215')
    scene.merged_mesh(parts, kinds={'printed'}).export(OUT / f'{NAME}-printed-parts.stl')


def validation():
    import checks
    report = {}
    n_parts, overlaps = checks.interference()
    report['interference'] = dict(method='exact B-rep intersection of every pair of parts, core + leg 1, '
                                  'modelled pose', parts=n_parts, overlapping_pairs=overlaps)
    chk = checks.Checker((0,))
    d, names = chk.clearance({0: (0, 0, 0)})
    report['modelled_pose'] = dict(min_clearance_mm=round(d, 2), closest=list(names))
    n, bad = checks.sweep_leg(step=3.0)
    report['concept_joint_ranges'] = dict(ranges_deg=layout.RANGES, step_deg=3.0, yaw_values=['min', 0, 'max'],
                                          poses=n, poses_with_contact=len(bad),
                                          contacts=[[list(p), h] for p, h in bad[:20]])
    report['free_travel_deg'] = dict(note='each joint alone from the modelled pose until the first contact, '
                                     '1 deg steps; the concept geometry alone gives the same hip and knee limits',
                                     **checks.joint_limits())
    report['neighbours'] = {f'legs 1 and 2 turned {a} deg towards each other': checks.neighbours(a) or 'clear'
                            for a in (20, 30)}
    concept = {}
    for key, fn in P.PRINTS.items():
        concept[key] = round(fn(1.0, servo=False).solid().Volume() / 1000, 4)
    report['concept_fidelity'] = dict(note='the generator with servo=False and scale 1 rebuilds the concept parts; '
                                      'volumes in cm3, compare final-concept/PRINT-BOM.csv', volumes=concept)
    cycle = gait.tripod(**GAIT)
    legs = checks.Checker(tuple(range(layout.LEGS)))
    contact = [n for n, (_, poses) in enumerate(cycle) if legs.collisions(dict(enumerate(poses)))]
    flat = [q for _, poses in cycle for q in poses]
    report['tripod_gait'] = dict(**GAIT, frames_with_contact=contact,
                                 min_clearance_mm=round(min(legs.clearance(dict(enumerate(p)))[0] for _, p in cycle), 2),
                                 joint_min_deg=[round(min(q[j] for q in flat), 1) for j in range(3)],
                                 joint_max_deg=[round(max(q[j] for q in flat), 1) for j in range(3)])
    report['solids'] = {k: dict(valid=v.isValid(), solids=len(v.Solids()), volume_cm3=round(v.Volume() / 1000, 2))
                        for k, v in A.shapes().items()}
    report['scale'] = layout.S
    report['servo'] = dict(model='Waveshare ST3215', count=18,
                           source='https://files.waveshare.com/upload/5/59/ST3215-3D.zip')
    with open(OUT / 'VALIDATION.json', 'w') as f:
        json.dump(report, f, indent=2)
    return report


# ------------------------------------------------------------------ renders
def _glb(parts, name):
    path = Path(tempfile.gettempdir()) / 'hx18-fc-st3215-render' / f'{name}.glb'
    path.parent.mkdir(parents=True, exist_ok=True)
    scene.export_glb(parts, path)
    return path


def render(jobs):
    """jobs: [(parts, png path, query, labels or None)], rendered in one browser."""
    tmp = Path(tempfile.gettempdir()) / 'hx18-fc-st3215-render'
    spec = []
    for n, (parts, png, query, labels) in enumerate(jobs):
        glb = _glb(parts, f'job{n}')
        if labels is not None:
            (tmp / f'job{n}-labels.json').write_text(json.dumps(labels))
            query += f'&labels=job{n}-labels.json'
        spec.append(dict(glb=str(glb), out=str(png), query=query))
    (tmp / 'jobs.json').write_text(json.dumps(spec))
    subprocess.run(['node', str(GEN / 'render' / 'render.mjs'), os.environ['HX18_NODE_MODULES'],
                    str(tmp / 'jobs.json')], check=True)


def servo_labels(parts):
    out = []
    for p in parts:
        if p.kind == 'servo' and p.name.endswith('/ top case'):
            c = layout.apply(p.loc, 12.0, 0.0, -18.6)
            label = p.name.split(' / ')[0]
            out.append(dict(p=[c.x, c.y, c.z], text=label.split(' ID ')[1], kind=label.split()[2]))
    return out


def _without(parts, *names):
    return [p for p in parts if not any(n in p.name for n in names)]


def renders(parts):
    r = OUT / 'renders'
    r.mkdir(exist_ok=True)
    open_parts = _without(parts, 'femur cover', 'Core lid', 'Lid screw')
    leg = [p for p in parts if p.name.startswith('Leg 1 ')]
    concept = concept_parts()
    lim = f'&dist={2.6 * 420:.0f}&target=0,0,70'
    render([
        (parts, r / 'HX18-final-concept-ST3215.png', 'dir=0.62,-0.68,0.5', None),
        (open_parts, r / 'HX18-ST3215-covers-off.png', 'dir=0.62,-0.68,0.62', None),
        (open_parts, r / 'HX18-ST3215-top.png', 'dir=0,0,1&up=1,0,0&ground=0', servo_labels(open_parts)),
        (parts, r / 'HX18-ST3215-underside.png', 'dir=0.35,-0.5,-1&ground=0', None),
        (leg, r / 'Leg.png', 'dir=0.2,1.2,0.55&ground=0', None),
        (_without(leg, 'femur cover'), r / 'Leg-cover-off.png', 'dir=0.2,1.2,0.55&ground=0', None),
        (_without(leg, 'femur cover', 'femur', 'cover screw'), r / 'Leg-servos.png', 'dir=0.25,1.2,0.6&ground=0', None),
        (concept, r / 'before.png', 'dir=0.62,-0.68,0.5&w=1200&h=900' + lim, None),
        (parts, r / 'after.png', 'dir=0.62,-0.68,0.5&w=1200&h=900' + lim, None),
    ])
    side_by_side(r / 'before.png', r / 'after.png', r / 'Before-after.png')


def concept_parts():
    """The original final concept (scale 1, servo envelopes as grey boxes), standing like the robot."""
    from scene import Part
    sh = {k: fn(1.0, servo=False).solid() for k, fn in P.PRINTS.items()}
    out = [Part(A.NAMES[k], sh[k], A.COLOURS[k]) for k in ('CoreTub', 'CoreLid', 'ElectronicsCassette')]
    # leg_shells.py reserves: actuator envelopes, 32 x 27 x 13 mm
    boxes = dict(base=((-22, -6.5, -28), (10, 6.5, -1)), hip=((-10, -13.5, -6.5), (22, 13.5, 6.5)),
                 knee=((30, -13.5, -6.5), (62, 13.5, 6.5)))
    for i in range(layout.LEGS):
        f = layout.frames(i, s=1.0)
        for key, link in (('CoxaCarrier', 'coxa'), ('FemurCarrier', 'femur'), ('FemurCheek', 'femur'),
                          ('Tibia', 'tibia'), ('FootPad', 'tibia')):
            out.append(Part(f'Leg {i + 1} {A.NAMES[key]}', sh[key], A.COLOURS[key], f[link]))
        for name, (lo, hi) in boxes.items():
            box = cq.Solid.makeBox(*(hi[j] - lo[j] for j in range(3)), cq.Vector(*lo))
            out.append(Part(f'{name} envelope', box, A.RESERVE, f['femur' if name != 'base' else 'base'],
                            'electronics'))
    low = min(layout.foot_point(i, s=1.0).z for i in range(layout.LEGS)) - 5.5
    return [Part(p.name, p.shape, p.color, cq.Location(cq.Vector(0, 0, -low)) * p.loc, p.kind) for p in out]


def side_by_side(left, right, out):
    from PIL import Image, ImageDraw, ImageFont
    a, b = Image.open(left).convert('RGB'), Image.open(right).convert('RGB')
    img = Image.new('RGB', (a.width + b.width, a.height + 70), (46, 52, 64))
    img.paste(a, (0, 70))
    img.paste(b, (a.width, 70))
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 34)
    except OSError:
        font = ImageFont.load_default()
    for x, text in ((0, 'final concept: servo envelopes (grey)'), (a.width, 'same design with 18 x ST3215, 1.4x')):
        w = d.textlength(text, font=font)
        d.text((x + (a.width - w) / 2, 18), text, fill=(229, 233, 240), font=font)
    img.save(out)
    left.unlink()
    right.unlink()


def walking_frames(only=None):
    """Placed parts of every gait frame, the body moved along the walking direction."""
    out = []
    for n, ((bx, by), poses) in enumerate(gait.tripod(**GAIT)):
        if only is not None and n not in only:
            continue
        parts = A.on_ground(A.robot([dict(yaw=a, hip=h, knee=k) for a, h, k in poses]))
        move = cq.Location(cq.Vector(bx, by, 0))
        out.append(((bx, by), [scene.Part(p.name, p.shape, p.color, move * p.loc, p.kind, p.metal, p.link)
                               for p in parts]))
    return out


def walk_gif(only=None, out=None):
    from PIL import Image
    tmp = Path(tempfile.gettempdir()) / 'hx18-fc-st3215-render'
    tile = 2 * GAIT['stride']
    jobs = []
    for n, ((bx, by), parts) in enumerate(walking_frames(only)):
        query = (f"dir={GIF_VIEW['dir']}&w=1920&h=1200&target={bx:.3f},{by:.3f},{GIF_VIEW['height']}"
                 f"&dist={GIF_VIEW['dist']}&floor={tile:g}&r=700")
        jobs.append((parts, tmp / f'walk-{n:02d}.png', query, None))
    render(jobs)
    frames = [Image.open(png).convert('RGB').resize((960, 600), Image.LANCZOS) for _, png, _, _ in jobs]
    if out is not None:                      # stills for checking the view
        for n, im in enumerate(frames):
            im.save(Path(out) / f'walk-still-{n}.png')
        return
    pal = Image.new('RGB', (960, 600 * 4))
    for k in range(4):
        pal.paste(frames[k * len(frames) // 4], (0, 600 * k))
    pal = pal.quantize(colors=255, method=Image.Quantize.MEDIANCUT)
    gif = [im.quantize(palette=pal, dither=Image.Dither.NONE) for im in frames]
    gif[0].save(OUT / 'renders' / 'HX18-ST3215-walk.gif', save_all=True, append_images=gif[1:],
                duration=40, loop=0, optimize=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--renders', action='store_true')
    ap.add_argument('--gif', action='store_true')
    ap.add_argument('--skip-cad', action='store_true')
    args = ap.parse_args()
    parts = A.on_ground(A.robot())
    if not args.skip_cad:
        for row in export_prints():
            print(row)
        export_cad(parts)
        rep = validation()
        print(json.dumps({k: rep[k] for k in ('interference', 'modelled_pose', 'free_travel_deg')}))
        print(rep['concept_joint_ranges']['poses'], 'poses,', rep['concept_joint_ranges']['poses_with_contact'],
              'with contact')
    if args.renders:
        renders(parts)
    if args.gif:
        walk_gif()


if __name__ == '__main__':
    sys.exit(main())
